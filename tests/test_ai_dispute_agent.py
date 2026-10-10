"""
Unit and Integration Tests for Autonomous LLM Dispute Fact-Finding & Mediation Agent.
Tests timeline analysis, scope creep detection, fault distribution, and escrow settlement recommendations.
"""

import uuid
import json
import pytest
from datetime import datetime, timezone, timedelta

from server.db.session import SessionLocal, Base, engine
from server.db.models import Profile, Project, Dispute, CreativeBrief, Conversation, Message
from server.services.ai_dispute_agent import AIDisputeAgent


@pytest.fixture(scope="module")
def setup_dispute_env():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create test brand and creator profiles
    brand_id = f"brand_{uuid.uuid4().hex[:8]}"
    creator_id = f"creator_{uuid.uuid4().hex[:8]}"

    uname_b = f"brand_disp_{uuid.uuid4().hex[:4]}"
    uname_c = f"creator_disp_{uuid.uuid4().hex[:4]}"
    brand = Profile(
        id=brand_id,
        username=uname_b,
        normalized_username=uname_b.lower(),
        password_hash="mock_hash",
        role="brand",
        display_name="Dispute Brand Studio"
    )
    creator = Profile(
        id=creator_id,
        username=uname_c,
        normalized_username=uname_c.lower(),
        password_hash="mock_hash",
        role="creator",
        display_name="Dispute Creator Studio"
    )
    db.add(brand)
    db.add(creator)
    db.commit()

    # Create project
    proj_id = f"proj_disp_{uuid.uuid4().hex[:8]}"
    deadline = datetime.now(timezone.utc) - timedelta(days=2) # 2 days overdue
    project = Project(
        id=proj_id,
        brand_id=brand_id,
        creator_id=creator_id,
        title="SuperBowl 30s Commercial",
        budget_amount=150000.0,
        currency="INR",
        deadline=deadline,
        status="disputed"
    )
    db.add(project)
    db.commit()

    # Conversation with scope creep
    conv = Conversation(
        id=f"conv_{uuid.uuid4().hex[:8]}",
        created_by=brand_id,
        project_id=proj_id
    )
    db.add(conv)
    db.commit()

    msg1 = Message(
        conversation_id=conv.id,
        sender_id=brand_id,
        body="Can you also make another video in vertical format and change script?"
    )
    msg2 = Message(
        conversation_id=conv.id,
        sender_id=creator_id,
        body="That was not in the agreed brief, that will require extra budget."
    )
    db.add(msg1)
    db.add(msg2)

    # Create dispute
    disp_id = f"disp_{uuid.uuid4().hex[:8]}"
    dispute = Dispute(
        id=disp_id,
        project_id=proj_id,
        filed_by_id=brand_id,
        against_id=creator_id,
        reason="quality_dispute",
        description="Creator missed deadline and output did not match creative vision."
    )
    db.add(dispute)
    db.commit()

    yield {"db": db, "dispute_id": disp_id, "project_id": proj_id, "brand_id": brand_id, "creator_id": creator_id}
    db.close()


def test_ai_dispute_agent_audit(setup_dispute_env):
    db = setup_dispute_env["db"]
    dispute_id = setup_dispute_env["dispute_id"]

    report = AIDisputeAgent.audit_dispute(db=db, dispute_id=dispute_id)

    assert report["dispute_id"] == dispute_id
    assert "fault_distribution" in report
    assert "brand_fault_percent" in report["fault_distribution"]
    assert "creator_fault_percent" in report["fault_distribution"]
    assert "recommended_settlement" in report

    settlement = report["recommended_settlement"]
    assert settlement["action"] in ("refund_to_brand", "release_to_creator", "split_50_50")
    assert settlement["confidence_score"] >= 0.80
    assert settlement["creator_payout_amount"] >= 0.0
    assert settlement["brand_refund_amount"] >= 0.0
    assert "arbitration_reasoning" in settlement
    assert len(settlement["arbitration_reasoning"]) > 20

    # Verify report was persisted on dispute record
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    assert dispute.ai_audit_report is not None
    assert dispute.ai_recommended_action == settlement["action"]
    assert dispute.ai_confidence_score == settlement["confidence_score"]
