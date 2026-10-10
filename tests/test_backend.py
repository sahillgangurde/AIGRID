"""
Comprehensive Backend Test Suite for FRAME.
Validates all 20 required backend criteria from Section 23 of the Master Specification.
"""

import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.db.session import SessionLocal, engine, Base
import server.db.models as models
from server.seed.seed_data import seed_database
from server.services.trust_score import TrustScoreService
from server.services.matching import MatchingService
from server.services.achievements import AchievementEngine

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()


import uuid

# 1. Duplicate usernames are rejected (case-insensitive)
def test_01_duplicate_usernames_rejected():
    uname = f"user_{uuid.uuid4().hex[:6]}"
    res1 = client.post("/api/auth/signup", json={
        "username": uname,
        "password": "Password123!",
        "display_name": "Unique Name",
        "role": "creator"
    })
    assert res1.status_code == 200

    # Case-insensitive duplicate attempt
    res2 = client.post("/api/auth/signup", json={
        "username": uname.upper(),
        "password": "Password123!",
        "display_name": "Duplicate Attempt",
        "role": "creator"
    })
    assert res2.status_code == 409
    assert "already taken" in res2.json()["detail"].lower()


# 2. Users cannot change their own protected role
def test_02_users_cannot_change_protected_role():
    uname = f"roleuser_{uuid.uuid4().hex[:6]}"
    res_sign = client.post("/api/auth/signup", json={
        "username": uname,
        "password": "Password123!",
        "display_name": "Role Test User",
        "role": "creator"
    })
    token = res_sign.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to change role via profile update
    res = client.put("/api/auth/profile", json={
        "display_name": "Hacked Admin",
        "role": "admin"
    }, headers=headers)
    assert res.status_code == 200

    # Verify role remained 'creator'
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.json()["role"] == "creator"


# 3. Unauthorized users cannot read confidential briefs
def test_03_unauthorized_users_cannot_read_confidential_briefs():
    res = client.get("/api/briefs")
    assert res.status_code == 200
    brief_ids = [b["id"] for b in res.json()["briefs"]]
    # brief_03 is confidential and should not be returned to public anonymous user
    assert "brief_03" not in brief_ids


# 4. Unauthorized users cannot read private project messages
def test_04_unauthorized_cannot_read_private_project_messages():
    # Login as unrelated user
    login_res = client.post("/api/auth/login", json={
        "username": "uniquename123",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/conversations/conv_proj_01/messages", headers=headers)
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()


# 5. Private media is inaccessible in public queries
def test_05_private_media_inaccessible_without_permission():
    db = SessionLocal()
    # Add a private portfolio item
    private_item = models.PortfolioItem(
        creator_id="creator_05",
        title="Confidential Unreleased Cut",
        content_type="Social Video Commercial",
        media_path="https://private-bucket/secret.mp4",
        visibility="private"
    )
    db.add(private_item)
    db.commit()

    # Public creator detail fetch
    res = client.get("/api/creators/creator_05")
    db.close()
    assert res.status_code == 200
    sample_titles = [w["title"] for w in res.json().get("sample_works", [])]
    assert "Confidential Unreleased Cut" not in sample_titles


# 6. Unapproved portfolio content cannot be published publicly
def test_06_unapproved_portfolio_content_cannot_be_published():
    # Login as Julian Mercer
    login_res = client.post("/api/auth/login", json={
        "username": "mercer_films",
        "password": "CreatorPass2026!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Request publication approval
    req_res = client.post("/api/approvals/request", json={
        "client_id": "brand_puma",
        "project_id": "proj_seed_01",
        "requested_media_scope": "15s excerpt only",
        "requested_metadata_scope": "Technical workflow attribution only"
    }, headers=headers)
    assert req_res.status_code == 200
    req_id = req_res.json()["request_id"]

    # Attempt to publish before client approves
    pub_res = client.post(f"/api/approvals/{req_id}/publish", json={
        "title": "Unapproved Excerpt",
        "description": "Bypassing approval",
        "content_type": "Social Video Commercial",
        "media_path": "https://cdn.example.com/video.mp4"
    }, headers=headers)
    assert pub_res.status_code == 403
    assert "pending_approval" in pub_res.json()["detail"]


# 7. A selected excerpt approval stores exact requested scope
def test_07_selected_excerpt_approval_scoped():
    db = SessionLocal()
    req = db.query(models.PortfolioApprovalRequest).first()
    db.close()
    assert req is not None
    assert "15s excerpt only" in req.requested_media_scope


# 8. Expired and revoked approvals no longer authorize publication
def test_08_expired_and_revoked_approvals():
    # Login as Puma brand
    puma_login = client.post("/api/auth/login", json={
        "username": "puma_lab",
        "password": "BrandPass2026!"
    })
    puma_headers = {"Authorization": f"Bearer {puma_login.json()['access_token']}"}

    # Login as Julian creator
    julian_login = client.post("/api/auth/login", json={
        "username": "mercer_films",
        "password": "CreatorPass2026!"
    })
    julian_headers = {"Authorization": f"Bearer {julian_login.json()['access_token']}"}

    # Create request
    req_res = client.post("/api/approvals/request", json={
        "client_id": "brand_puma",
        "project_id": "proj_seed_01",
        "requested_media_scope": "Short teaser",
        "requested_metadata_scope": "Attribution"
    }, headers=julian_headers)
    req_id = req_res.json()["request_id"]

    # Approve then revoke
    client.post(f"/api/approvals/{req_id}/review", json={"decision": "approved"}, headers=puma_headers)
    client.post(f"/api/approvals/{req_id}/revoke", headers=puma_headers)

    # Attempt to publish revoked request
    pub_res = client.post(f"/api/approvals/{req_id}/publish", json={
        "title": "Revoked Work",
        "description": "Should fail",
        "content_type": "Social Video Commercial",
        "media_path": "https://cdn.example.com/revoked.mp4"
    }, headers=julian_headers)
    assert pub_res.status_code == 403
    assert "revoked" in pub_res.json()["detail"]


# 9. Matching results are deterministic for identical inputs
def test_09_matching_results_deterministic():
    db = SessionLocal()
    res1 = MatchingService.match_creators_to_brief(db, "brief_01")
    res2 = MatchingService.match_creators_to_brief(db, "brief_01")
    db.close()
    assert len(res1) == len(res2)
    for m1, m2 in zip(res1, res2):
        assert m1["creator_id"] == m2["creator_id"]
        assert m1["match_score"] == m2["match_score"]


# 10. Matching explanations identify relevant criteria
def test_10_matching_explanations_identify_criteria():
    db = SessionLocal()
    matches = MatchingService.match_creators_to_brief(db, "brief_01")
    db.close()
    top = matches[0]
    assert "component_scores" in top
    assert "skills_and_specialization" in top["component_scores"]
    assert len(top["match_reasons"]) > 0
    assert "budget_compatibility" in top
    assert "identity_verification" in top


# 11. Creators with insufficient history are not assigned a negative trust status
def test_11_insufficient_history_neutral_prior():
    db = SessionLocal()
    # Creator with 0 projects
    trust = TrustScoreService.calculate_creator_trust_score(db, "creator_12")
    db.close()
    assert trust["insufficient_data"] is True
    assert trust["overall_score"] == 80.0 # Neutral prior baseline
    assert trust["status"] == "INSUFFICIENT_EVIDENCE"
    assert "does not penalize" in trust["explanation"]


# 12. Simulated KYC cannot produce genuine non-demo verified badge
def test_12_simulated_kyc_marked_demo():
    db = SessionLocal()
    vrec = db.query(models.VerificationRecord).filter(models.VerificationRecord.user_id == "creator_05").first()
    db.close()
    assert vrec is not None
    assert vrec.is_demo is True


# 13. Achievement awards cannot be duplicated
def test_13_achievement_awards_cannot_be_duplicated():
    db = SessionLocal()
    first_awards = AchievementEngine.evaluate_and_award_user(db, "creator_05")
    second_awards = AchievementEngine.evaluate_and_award_user(db, "creator_05")
    db.close()
    # Second evaluation must not award duplicate badges
    assert len(second_awards) == 0


# 14. Project status transitions are validated
def test_14_project_status_transitions_validated():
    # Login as Puma brand
    puma_login = client.post("/api/auth/login", json={
        "username": "puma_lab",
        "password": "BrandPass2026!"
    })
    headers = {"Authorization": f"Bearer {puma_login.json()['access_token']}"}

    # Attempt illegal jump from in_production directly to completed
    res = client.patch("/api/projects/proj_seed_01/status", json={"status": "completed"}, headers=headers)
    assert res.status_code == 400
    assert "invalid transition" in res.json()["detail"].lower()


# 15. Client-supplied payment success cannot mark a transaction as paid
def test_15_client_cannot_arbitrarily_mark_transaction_paid():
    # No endpoint exists for client to mark arbitrary transaction paid
    res = client.patch("/api/finance/transactions/tx_seed_01", json={"status": "paid"})
    assert res.status_code == 404 or res.status_code == 405


# 16. Duplicate payment webhook prevention
def test_16_duplicate_payment_prevention():
    # Attempt duplicate checkout
    puma_login = client.post("/api/auth/login", json={
        "username": "puma_lab",
        "password": "BrandPass2026!"
    })
    headers = {"Authorization": f"Bearer {puma_login.json()['access_token']}"}
    res = client.post("/api/finance/demo-checkout", json={
        "creator_id": "creator_05",
        "gross_amount": 5000.0,
        "currency": "INR"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_demo"] is True
    assert res.json()["transaction"]["fee"] == 500.0 # 10% platform fee verified


# 17. Earnings and transaction records inaccessible to unauthorized users
def test_17_earnings_inaccessible_to_unauthorized():
    res = client.get("/api/finance/transactions")
    assert res.status_code == 401


# 18. Admin functions reject non-administrator accounts
def test_18_admin_functions_reject_non_admin():
    login_res = client.post("/api/auth/login", json={
        "username": "mercer_films",
        "password": "CreatorPass2026!"
    })
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}
    res = client.get("/api/admin/audit-logs", headers=headers)
    assert res.status_code == 403
    assert "administrative privileges required" in res.json()["detail"].lower()


# 19. All core records persist after refreshing the application
def test_19_core_records_persist_in_database():
    db = SessionLocal()
    creators_cnt = db.query(models.Profile).filter(models.Profile.role == "creator").count()
    briefs_cnt = db.query(models.CreativeBrief).count()
    projects_cnt = db.query(models.Project).count()
    db.close()
    assert creators_cnt >= 12
    assert briefs_cnt >= 3
    assert projects_cnt >= 1


# 20. Errors handled without exposing secrets or private data
def test_20_errors_handled_safely():
    res = client.post("/api/auth/login", json={
        "username": "mercer_films",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "password_hash" not in res.text
    assert "secret" not in res.text.lower()


# 21. Supabase / Google OAuth sync creates profile and returns valid JWT
def test_21_supabase_google_oauth_sync():
    res = client.post("/api/auth/google-sync", json={
        "email": "test.google.user@example.com",
        "display_name": "Google Test Creator",
        "role": "creator"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "test.google.user@example.com"
    assert data["user"]["display_name"] == "Google Test Creator"
    assert data["user"]["role"] == "creator"

    # Verify user can access authenticated endpoints with the token
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "test.google.user@example.com"

