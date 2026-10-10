"""
Subscription Free-Trial Enforcement Tests — CreatorGrid revenue stream #2.

Covers:
  - Creator signup par free-trial subscription create hoti hai (90-day trial)
  - Trial status payload (show_banner)
  - Expired trial → is_listed=False, creator directory/search se hidden
  - Upgrade to pro_creator → listing restored
  - Creator-custom advance request → brand approve → project.advance_amount replaced
  - Price-negotiation PII pattern (₹ amounts blocked in chat)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.db.session import SessionLocal, engine, Base
from server.services.subscription_service import SubscriptionService, FREE_TRIAL_DAYS

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    from server.seed.seed_data import seed_database
    try:
        seed_database(db)
    except Exception:
        pass
    db.close()
    yield


def _signup(role, name):
    uname = f"sub_{role}_{uuid.uuid4().hex[:8]}"
    res = client.post("/api/auth/signup", json={
        "username": uname,
        "password": "Password123!",
        "display_name": name,
        "role": role,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    return body["user"], body["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _create_project(brand, token, creator_id):
    res = client.post("/api/projects", json={
        "creator_id": creator_id,
        "title": "Subscription Test Project",
        "budget_amount": 120000.0,
        "currency": "INR",
    }, headers=_auth(token))
    assert res.status_code == 200, res.text
    return res.json()["project"]


# ── 1. Free trial created at signup ──────────────────────────

def test_creator_gets_90day_free_trial():
    user, token = _signup("creator", "Trial Creator")
    res = client.get("/api/subscriptions/me", headers=_auth(token))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["role"] == "creator"
    assert body["plan_code"] == "free_creator"
    assert body["trial_active"] is True
    assert body["days_left"] is not None and body["days_left"] <= FREE_TRIAL_DAYS
    assert body["is_listed"] is True
    assert body["show_banner"] is False  # far from expiry


def test_brand_has_no_trial():
    user, token = _signup("brand", "Trial Brand")
    res = client.get("/api/subscriptions/me", headers=_auth(token))
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "brand"
    assert body["trial_active"] is False


# ── 2. Expired trial → listing paused ────────────────────────

def test_expired_trial_hides_creator_from_directory():
    user, token = _signup("creator", "Expiring Creator")
    # Force-expire via the demo endpoint
    res = client.post("/api/subscriptions/demo-expire-trial", headers=_auth(token))
    assert res.status_code == 200, res.text
    assert res.json()["is_listed"] is False

    # Status reflects expiry
    status = client.get("/api/subscriptions/me", headers=_auth(token)).json()
    assert status["is_listed"] is False
    assert status["trial_active"] is False
    assert status["show_banner"] is True

    # Hidden from public directory
    directory = client.get("/api/creators").json()["creators"]
    assert all(c["id"] != user["id"] for c in directory)


def test_upgrade_restores_listing():
    user, token = _signup("creator", "Upgrading Creator")
    client.post("/api/subscriptions/demo-expire-trial", headers=_auth(token))
    assert client.get("/api/subscriptions/me", headers=_auth(token)).json()["is_listed"] is False

    res = client.post("/api/subscriptions/upgrade", json={"plan_code": "pro_creator"},
                      headers=_auth(token))
    assert res.status_code == 200, res.text
    assert res.json()["subscription"]["is_listed"] is True

    status = client.get("/api/subscriptions/me", headers=_auth(token)).json()
    assert status["plan_code"] == "pro_creator"
    assert status["is_listed"] is True
    assert status["show_banner"] is False

    # Back in the directory
    directory = client.get("/api/creators").json()["creators"]
    assert any(c["id"] == user["id"] for c in directory)


# ── 3. Creator-custom advance request flow ───────────────────

def test_custom_advance_request_flow():
    brand, brand_tok = _signup("brand", "AdvReq Brand")
    creator, creator_tok = _signup("creator", "AdvReq Creator")
    project = _create_project(brand, brand_tok, creator["id"])

    # Creator sets a quote (defines escrow staging)
    client.post(f"/api/projects/{project['id']}/quote",
                json={"creator_quote": 100000.0, "markup_percent": 0.20},
                headers=_auth(creator_tok))

    # Creator requests a CUSTOM advance (not the fixed ₹20k)
    res = client.post(f"/api/projects/{project['id']}/advance-request",
                      json={"amount": 35000.0, "reason": "Custom LoRA fine-tune compute upfront"},
                      headers=_auth(creator_tok))
    assert res.status_code == 200, res.text
    req_body = res.json()["request"]
    assert req_body["amount"] == 35000.0
    assert req_body["status"] == "pending"

    # Brand cannot create a request; creator cannot decide
    res_brand_create = client.post(f"/api/projects/{project['id']}/advance-request",
                                   json={"amount": 1000.0}, headers=_auth(brand_tok))
    assert res_brand_create.status_code == 403

    # Brand approves
    res_dec = client.post(f"/api/projects/advance-requests/{req_body['id']}/decision",
                          json={"action": "approve", "note": "Compute cost justified"},
                          headers=_auth(brand_tok))
    assert res_dec.status_code == 200, res_dec.text
    assert res_dec.json()["status"] == "approved"
    assert res_dec.json()["project_advance_amount"] == 35000.0

    # Advance deposit now locks at the CUSTOM amount
    res_dep = client.post(f"/api/projects/{project['id']}/advance-deposit",
                          json={}, headers=_auth(brand_tok))
    assert res_dep.status_code == 200, res_dep.text
    assert res_dep.json()["transaction"]["amount"] == 35000.0
    assert res_dep.json()["escrow_state"] == "advance_locked"


def test_advance_request_rejection():
    brand, brand_tok = _signup("brand", "AdvRej Brand")
    creator, creator_tok = _signup("creator", "AdvRej Creator")
    project = _create_project(brand, brand_tok, creator["id"])

    res = client.post(f"/api/projects/{project['id']}/advance-request",
                      json={"amount": 50000.0}, headers=_auth(creator_tok))
    req_id = res.json()["request"]["id"]

    res_dec = client.post(f"/api/projects/advance-requests/{req_id}/decision",
                          json={"action": "reject", "note": "Too high for scope"},
                          headers=_auth(brand_tok))
    assert res_dec.status_code == 200
    assert res_dec.json()["status"] == "rejected"

    reqs = client.get(f"/api/projects/{project['id']}/advance-requests",
                      headers=_auth(brand_tok)).json()["requests"]
    assert any(r["id"] == req_id and r["status"] == "rejected" for r in reqs)


def test_advance_request_validation():
    brand, brand_tok = _signup("brand", "AdvVal Brand")
    creator, creator_tok = _signup("creator", "AdvVal Creator")
    project = _create_project(brand, brand_tok, creator["id"])

    # Amount ≥ budget rejected
    res = client.post(f"/api/projects/{project['id']}/advance-request",
                      json={"amount": 120000.0}, headers=_auth(creator_tok))
    assert res.status_code == 400

    # Negative rejected
    res = client.post(f"/api/projects/{project['id']}/advance-request",
                      json={"amount": -5}, headers=_auth(creator_tok))
    assert res.status_code == 400


# ── 4. Price-negotiation PII pattern ─────────────────────────

def test_price_negotiation_blocked_in_chat_scan():
    from server.middleware.pii_interceptor import PIIInterceptor
    has_pii, cleaned, violations = PIIInterceptor.scan("Final price ₹1,00,000 hai")
    assert has_pii is True
    assert "1,00,000" not in cleaned
    assert any(v["type"] == "price_negotiation" for v in violations)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
