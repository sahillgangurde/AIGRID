"""
Subscription Free-Trial Enforcement Service — CreatorGrid revenue model.

Creator listing lifecycle:
  1. Signup → Subscription(plan_code='free_creator', trial_start=now, trial_end=now+90d)
  2. During trial → is_listed=True, creator appears in directory/search/brief matching.
  3. Trial expiring (≤7 days left) → warning banner data available to frontend.
  4. Trial expired & not upgraded → is_listed=False (auto on any status check) and
     creator is filtered OUT of directory, search, and brief matching.
  5. Upgrade to pro_creator (paid) → is_listed=True again, trial fields cleared.

Usage:
    from server.services.subscription_service import SubscriptionService
    sub = SubscriptionService.ensure_subscription(db, profile)     # get-or-create
    status = SubscriptionService.get_status(db, profile_id)        # dict for UI banner
    SubscriptionService.upgrade(db, profile_id, "pro_creator")     # end trial
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy.orm import Session
from server.db.models import Profile, Subscription

logger = logging.getLogger(__name__)

FREE_TRIAL_DAYS = 90          # pitch: "1-3 months free listing" → 90 days
TRIAL_EXPIRY_WARNING_DAYS = 7
PRO_PLAN_CODES = {"pro_creator", "studio_creator"}
FREE_PLAN_CODE = "free_creator"


def _utcnow():
    return datetime.now(timezone.utc)


def _as_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """SQLite returns naive datetimes — re-attach UTC before comparison."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class SubscriptionService:

    # ── Core lifecycle ────────────────────────────────────────

    @classmethod
    def ensure_subscription(cls, db: Session, profile: Profile) -> Subscription:
        """Get-or-create the subscription for a profile (creator or brand)."""
        if not profile:
            raise ValueError("profile required")

        sub = db.query(Subscription).filter(Subscription.user_id == profile.id).first()
        if sub:
            return sub

        is_creator = getattr(profile, "role", None) == "creator"
        now = datetime.now(timezone.utc)

        sub = Subscription(
            user_id=profile.id,
            plan_code=FREE_PLAN_CODE if is_creator else "studio_brand",
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=FREE_TRIAL_DAYS if is_creator else 365),
            # Brands don't go through a creator trial.
            trial_start=now if is_creator else None,
            trial_end=(now + timedelta(days=FREE_TRIAL_DAYS)) if is_creator else None,
            is_listed=True,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @classmethod
    def refresh_listing(cls, db: Session, sub: Subscription) -> Subscription:
        """
        Recompute is_listed from trial state. Call whenever a creator's
        subscription is read before listing surfaces (directory/search/matching).
        """
        if sub.plan_code in PRO_PLAN_CODES:
            sub.is_listed = True
            sub.status = "active"
        elif sub.plan_code == FREE_PLAN_CODE and sub.trial_end:
            expired = _as_aware(sub.trial_end) < _utcnow()
            sub.is_listed = not expired
            sub.status = "trial_expired" if expired else "trial_active"
        db.commit()
        return sub

    @classmethod
    def upgrade(cls, db: Session, user_id: str, plan_code: str = "pro_creator",
                provider_reference: Optional[str] = None) -> Subscription:
        """Upgrade creator to a paid plan — clears the trial and re-lists."""
        sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if not sub:
            profile = db.query(Profile).filter(Profile.id == user_id).first()
            if not profile:
                raise ValueError("User not found")
            sub = cls.ensure_subscription(db, profile)

        sub.plan_code = plan_code
        sub.status = "active"
        sub.is_listed = True
        if provider_reference:
            sub.billing_provider = "razorpay"
            sub.provider_subscription_reference = provider_reference
        now = datetime.now(timezone.utc)
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=365)
        sub.trial_start = None
        sub.trial_end = None
        db.commit()
        db.refresh(sub)
        return sub

    # ── Queries for listing enforcement ───────────────────────

    @classmethod
    def is_listed(cls, db: Session, user_id: str) -> bool:
        """Whether a creator may appear in directory/search/matching right now."""
        sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
        if sub is None:
            return True  # legacy creators without a subscription row stay listed
        if sub.plan_code in PRO_PLAN_CODES:
            return True
        if sub.plan_code == FREE_PLAN_CODE:
            trial_end = _as_aware(sub.trial_end)
            return bool(trial_end and trial_end >= _utcnow())
        return True

    # ── Status payload for frontend banner ────────────────────

    @classmethod
    def get_status(cls, db: Session, user_id: str) -> Dict[str, Any]:
        """Status dict used by the creator dashboard / profile banner."""
        profile = db.query(Profile).filter(Profile.id == user_id).first()
        if not profile:
            return {"error": "user_not_found"}

        sub = cls.ensure_subscription(db, profile)
        sub = cls.refresh_listing(db, sub)
        now = datetime.now(timezone.utc)

        if profile.role != "creator":
            return {
                "role": "brand",
                "plan_code": sub.plan_code,
                "is_listed": True,
                "trial_active": False,
                "days_left": None,
                "show_banner": False,
            }

        trial_end = _as_aware(sub.trial_end)
        days_left = max(0, (trial_end - now).days) if trial_end else None

        trial_active = bool(trial_end and trial_end >= now)
        expiring_soon = trial_active and days_left is not None and days_left <= TRIAL_EXPIRY_WARNING_DAYS

        return {
            "role": "creator",
            "plan_code": sub.plan_code,
            "status": sub.status,
            "is_listed": sub.is_listed,
            "trial_active": trial_active,
            "trial_start": sub.trial_start.isoformat() if sub.trial_start else None,
            "trial_end": trial_end.isoformat() if trial_end else None,
            "days_left": days_left,
            "expiring_soon": expiring_soon,
            "show_banner": days_left is not None and days_left <= TRIAL_EXPIRY_WARNING_DAYS,
        }

    # ── Filter helper for list endpoints ──────────────────────

    @classmethod
    def filter_listed_creators(cls, db: Session, profiles: List[Profile]) -> List[Profile]:
        """
        Filters a list of creator Profiles to those with an active listing.
        No subscription row (legacy data) → treated as listed.
        """
        subs = {s.user_id: s for s in db.query(Subscription).filter(
            Subscription.user_id.in_([p.id for p in profiles]) if profiles else Subscription.user_id.is_(None)
        ).all()}

        now = _utcnow()
        listed = []
        for p in profiles:
            sub = subs.get(p.id)
            if sub is None:
                listed.append(p)
            elif sub.plan_code in PRO_PLAN_CODES:
                listed.append(p)
            elif sub.plan_code == FREE_PLAN_CODE:
                trial_end = _as_aware(sub.trial_end)
                if trial_end and trial_end >= now:
                    listed.append(p)
            else:
                listed.append(p)
        return listed
