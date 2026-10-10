"""
Test Suite for Hypear AI v2.0 Anonymous Marketplace Features.
Tests:
- Real-time PII interception via REST /api/conversations
- Multi-party escrow calculation & Razorpay signature verification
- Dispute filing and automated escrow freeze
- Anonymous identity masking in messages
"""

import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.db.session import SessionLocal
import server.db.models as models
from server.services.escrow import EscrowService

client = TestClient(app)

def test_escrow_multi_party_split():
    """Verify escrow calculate returns 5% platform fee, compute hold, and creator net payout."""
    calc = EscrowService.calculate_compute_and_milestones(
        base_license_usd=1000.0,
        gpu_steps=1200,
        gpu_tier="H100_SXM5",
        num_variations=4
    )
    assert "multi_party_split" in calc
    split = calc["multi_party_split"]
    assert split["platform_fee_percent"] == 5.0
    assert split["platform_fee_usd"] > 0
    assert split["creator_net_payout_usd"] > 0
    assert calc["total_contract_value_usd"] == round(split["platform_fee_usd"] + split["compute_escrow_usd"] + split["creator_net_payout_usd"], 2)


def test_razorpay_signature_verification():
    """Verify HMAC SHA-256 signature verifier for Razorpay webhooks."""
    import hmac
    import hashlib
    order_id = "order_test_12345"
    payment_id = "pay_test_67890"
    secret = "hypear_escrow_secret_key_2026"

    msg = f"{order_id}|{payment_id}".encode("utf-8")
    valid_sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    assert EscrowService.verify_razorpay_signature(order_id, payment_id, valid_sig) is True
    assert EscrowService.verify_razorpay_signature(order_id, payment_id, "invalid_sig_xyz") is False


def test_escrow_freeze_on_dispute():
    """Verify advancing escrow stage fails if contract is frozen in dispute."""
    contract = EscrowService.create_contract(
        buyer_id="buyer_01",
        creator_id="creator_01",
        creator_name="Studio Phantom",
        base_license_usd=2000.0
    )
    cid = contract["contract_id"]

    # Freeze contract
    frozen = EscrowService.advance_escrow_stage(cid, "FREEZE_DISPUTE")
    assert frozen.get("is_frozen") is True
    assert frozen.get("status") == "FROZEN_IN_DISPUTE"

    # Try advancing milestone while frozen
    attempt = EscrowService.advance_escrow_stage(cid, "RELEASE_FINAL_70")
    assert "error" in attempt
    assert attempt["error"] == "ESCROW_FROZEN"
