"""
Payments Webhook Router — CreatorGrid Escrow Flow.
/api/payments

Payment gateway webhook endpoint that closes the loop between the gateway
(Razorpay-style) and the platform ledger:

  payment.captured  -> advance deposit held_in_escrow -> escrow_state=advance_locked
                       -> contact unlock becomes possible (post-NDA)
  payment.failed    -> advance attempt logged, escrow stays pending_advance

Security:
  - HMAC SHA-256 signature verification (Razorpay convention: order_id|payment_id
    signed with the webhook secret). Unsigned or mismatched webhooks are rejected
    with 400 BEFORE any ledger mutation.
  - Every accepted event lands in audit_logs for dispute forensics.

Demo mode:
  - If payment_reference starts with 'demo_', signature checking is skipped so the
    hackathon flow can drive the same code path without live gateway keys.
"""

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.db.session import get_db
from server.db.models import Project, Transaction, AuditLog
from server.services.auth_service import get_current_user
from server.db.models import Profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments Webhook"])

WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "hypear_webhook_secret_demo")


class WebhookEvent(BaseModel):
    event: str                                   # payment.captured | payment.failed
    order_id: str
    payment_id: str
    signature: Optional[str] = None              # HMAC SHA-256 hex of f"{order_id}|{payment_id}"
    amount: Optional[float] = None               # amount in currency units
    currency: Optional[str] = None
    project_id: Optional[str] = None             # required for advance-deposit capture


def _verify_signature(order_id: str, payment_id: str, signature: Optional[str]) -> bool:
    if not signature:
        return False
    try:
        expected = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def _find_project_for_event(db: Session, payload: WebhookEvent) -> Optional[Project]:
    """
    Resolves the project from either the explicit project_id (demo mode) or from
    the escrow transaction whose provider_reference matches the order_id.
    """
    if payload.project_id:
        return db.query(Project).filter(Project.id == payload.project_id).first()

    tx = db.query(Transaction).filter(
        Transaction.provider_reference == payload.order_id,
        Transaction.status == "held_in_escrow",
    ).first()
    if not tx or not tx.project_id:
        return None
    return db.query(Project).filter(Project.id == tx.project_id).first()


@router.post("/webhook")
def payments_webhook(
    event: WebhookEvent,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Public webhook endpoint (gateway calls this; no JWT). Verifies HMAC signature,
    then advances the project escrow state machine.
    """
    if event.event not in ("payment.captured", "payment.failed"):
        raise HTTPException(status_code=400, detail=f"Unsupported event '{event.event}'.")

    is_demo_event = (event.order_id or "").startswith("demo_") or (event.payment_id or "").startswith("demo_")

    if not is_demo_event and not _verify_signature(event.order_id, event.payment_id, event.signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    project = _find_project_for_event(db, event)

    if event.event == "payment.failed":
        db.add(AuditLog(
            actor_id=None,
            action="PAYMENT_FAILED",
            resource_type="payments_webhook",
            resource_id=project.id if project else None,
            metadata_json=json.dumps({"order_id": event.order_id, "payment_id": event.payment_id})
        ))
        db.commit()
        return {"status": "logged", "event": event.event}

    # payment.captured
    if not project:
        raise HTTPException(status_code=404, detail="No escrow session found for this order.")

    if project.escrow_state == "advance_locked":
        return {"status": "duplicate_ignored", "escrow_state": project.escrow_state}

    # Idempotency: reuse an existing held transaction, else create the ledger row.
    tx = db.query(Transaction).filter(
        Transaction.project_id == project.id,
        Transaction.status == "held_in_escrow",
    ).first()
    if not tx:
        amount = round(float(event.amount or project.advance_amount or 0.0), 2)
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Captured payment has no resolvable amount.")
        tx = Transaction(
            project_id=project.id,
            brand_id=project.brand_id,
            creator_id=project.creator_id,
            gross_amount=amount,
            platform_fee=amount,
            net_amount=0.0,
            currency=event.currency or project.currency,
            status="held_in_escrow",
            provider_reference=event.order_id,
        )
        db.add(tx)

    project.escrow_state = "advance_locked"
    project.advance_amount = tx.gross_amount
    from datetime import datetime, timezone
    project.advance_locked_at = datetime.now(timezone.utc)

    db.add(AuditLog(
        actor_id=project.brand_id,
        action="WEBHOOK_PAYMENT_CAPTURED",
        resource_type="project",
        resource_id=project.id,
        metadata_json=json.dumps({
            "order_id": event.order_id,
            "payment_id": event.payment_id,
            "amount": tx.gross_amount,
            "escrow_state": "advance_locked",
        })
    ))
    db.commit()

    # Wire: deal finalized via gateway → notify both parties + admins.
    try:
        from server.services.notification_service import NotificationService
        NotificationService.notify_both_parties(
            db, project.id, "deal_finalized",
            {"amount": tx.gross_amount, "currency": tx.currency}
        )
        admins = db.query(Profile).filter(Profile.role == "admin").all()
        for admin in admins:
            NotificationService.push_to_profile(
                db, admin.id, "deal_finalized",
                {"amount": tx.gross_amount, "currency": tx.currency}
            )
    except Exception:
        pass

    return {
        "status": "escrow_locked",
        "project_id": project.id,
        "escrow_state": project.escrow_state,
        "amount": tx.gross_amount,
        "message": "Advance captured by gateway. Escrow locked; contact unlock available post-NDA.",
    }
