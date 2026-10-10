"""
Subscription & Free-Trial Router — CreatorGrid revenue stream #2.

/api/subscriptions
  GET  /me                 → trial status for logged-in user (banner data)
  POST /upgrade            → upgrade creator to a paid plan (demo checkout)
  POST /demo-expire-trial  → demo helper: force trial expiry (testing/QA only)
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.db.session import get_db
from server.db.models import Profile, Subscription, AuditLog
from server.services.auth_service import get_current_user
from server.services.subscription_service import (
    SubscriptionService, FREE_TRIAL_DAYS, FREE_PLAN_CODE
)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions & Free Trial"])


class UpgradeRequest(BaseModel):
    plan_code: str = "pro_creator"
    provider_reference: Optional[str] = None  # Razorpay subscription id once live


@router.get("/me")
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Trial listing status — drives the 'Free trial ends in X days' banner."""
    return SubscriptionService.get_status(db, current_user.id)


@router.post("/upgrade")
def upgrade_subscription(
    req: UpgradeRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Upgrade creator from free trial to a paid listing plan.
    Demo mode: marks the subscription paid immediately (Razorpay subscription
    reference can be threaded through once the live gateway is wired).
    """
    if req.plan_code not in ("pro_creator", "studio_creator"):
        raise HTTPException(status_code=400, detail="plan_code must be 'pro_creator' or 'studio_creator'.")

    sub = SubscriptionService.upgrade(
        db,
        user_id=current_user.id,
        plan_code=req.plan_code,
        provider_reference=req.provider_reference or f"DEMO_SUB_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    )
    db.add(AuditLog(
        actor_id=current_user.id,
        action="SUBSCRIPTION_UPGRADED",
        resource_type="subscription",
        resource_id=sub.id,
        metadata_json=json.dumps({"plan_code": sub.plan_code, "is_demo": True})
    ))
    db.commit()

    return {
        "status": "upgraded",
        "subscription": {
            "plan_code": sub.plan_code,
            "status": sub.status,
            "is_listed": sub.is_listed,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None
        },
        "is_demo": True
    }


@router.post("/demo-expire-trial")
def demo_expire_trial(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    QA/demo helper: force the current user's free trial to be expired so the
    listing-pause flow can be exercised end-to-end without waiting 90 days.
    """
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub:
        sub = SubscriptionService.ensure_subscription(db, current_user)
    if sub.plan_code != FREE_PLAN_CODE:
        raise HTTPException(status_code=409, detail="Only free-trial subscriptions can be expired.")
    sub.trial_end = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    SubscriptionService.refresh_listing(db, sub)
    return {"status": "trial_expired", "is_listed": sub.is_listed}
