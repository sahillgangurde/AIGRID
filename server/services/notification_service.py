"""
Notification Service — Hypear AI v2.0.

Unified notification dispatch via:
  - Firebase Cloud Messaging (FCM) — mobile/web push notifications
  - SendGrid — transactional email

Event Types and Templates:
  message_received      → "💬 New message from {alias}"
  milestone_approved    → "✅ Milestone approved — ₹{amount} released"
  milestone_pending     → "⏳ Milestone awaiting approval"
  payment_received      → "💰 Payment received: ₹{amount}"
  dispute_filed         → "⚠️ Dispute filed on your project"
  dispute_resolved      → "✅ Dispute resolved: {action}"
  kyc_verified          → "🎉 Identity verified!"
  kyc_rejected          → "❌ KYC verification failed"
  pii_violation         → "🚫 Message blocked: contact info detected"
  nda_signed            → "📝 NDA signed — identity reveal enabled"
  brief_match           → "🎯 You matched a new brief: {brief_title}"

Usage:
    from server.services.notification_service import NotificationService
    await NotificationService.push(fcm_token, "message_received", {"alias": "Studio Phantom"})
    await NotificationService.email(to="user@hypear.ai", event="kyc_verified", data={})
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── FCM Setup (Firebase Admin SDK) ───────────────────────────
_firebase_initialized = False

def _init_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials

        sa_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        if not sa_json:
            logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON not set — FCM push disabled.")
            return False

        import json
        cred = credentials.Certificate(json.loads(sa_json))
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        return False


# ── Event Templates ───────────────────────────────────────────

PUSH_TEMPLATES: Dict[str, Dict[str, str]] = {
    "message_received": {
        "title": "Hypear AI • New Message",
        "body": "💬 New message from {alias}"
    },
    "milestone_approved": {
        "title": "Hypear AI • Payment Released",
        "body": "✅ Milestone approved — ₹{amount} is on its way"
    },
    "milestone_pending": {
        "title": "Hypear AI • Action Required",
        "body": "⏳ Your milestone delivery is awaiting brand approval"
    },
    "payment_received": {
        "title": "Hypear AI • Payment Received",
        "body": "💰 ₹{amount} has been credited to your payout"
    },
    "dispute_filed": {
        "title": "Hypear AI • Dispute Alert",
        "body": "⚠️ A dispute has been filed on project #{project_id}. Escrow frozen."
    },
    "dispute_resolved": {
        "title": "Hypear AI • Dispute Resolved",
        "body": "✅ Dispute resolved: {action}"
    },
    "kyc_verified": {
        "title": "Hypear AI • Identity Verified 🎉",
        "body": "Your identity is verified. You're now a trusted creator."
    },
    "kyc_rejected": {
        "title": "Hypear AI • Verification Failed",
        "body": "❌ KYC rejected. Please re-submit with valid documents."
    },
    "pii_violation": {
        "title": "Hypear AI • Message Blocked",
        "body": "🚫 Contact info was detected and removed to protect anonymity."
    },
    "nda_signed": {
        "title": "Hypear AI • NDA Signed",
        "body": "📝 Both parties signed. Identity reveal is now available for project #{project_id}."
    },
    "brief_match": {
        "title": "Hypear AI • New Match 🎯",
        "body": "You matched a new brief: {brief_title}"
    },
    "deal_finalized": {
        "title": "Hypear AI • Deal Finalized 🤝",
        "body": "Advance deposit locked in escrow for project #{project_id}. Contact reveal is now unlocked post-NDA."
    },
    "advance_requested": {
        "title": "Hypear AI • Advance Request Received",
        "body": "Creator requested a ₹{amount} {currency} advance on project #{project_id}. Review and approve."
    },
}

EMAIL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "kyc_verified": {
        "subject": "🎉 Your Hypear AI identity is verified",
        "html": """
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto;padding:32px;">
          <h1 style="color:#4f46e5;">Identity Verified ✅</h1>
          <p>Your KYC verification is complete. You now have a verified badge on Hypear AI.</p>
          <p>As a verified creator, you can accept higher-value projects and your trust score increases automatically.</p>
          <a href="https://hypear.ai/dashboard" style="background:#4f46e5;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;">Go to Dashboard</a>
        </div>
        """
    },
    "dispute_filed": {
        "subject": "⚠️ A dispute has been filed on your project",
        "html": """
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto;padding:32px;">
          <h1 style="color:#ef4444;">Dispute Alert</h1>
          <p>A dispute has been filed on project <strong>#{project_id}</strong>.</p>
          <p>Your escrow funds are temporarily frozen while our team reviews the case.</p>
          <p>Log in to upload evidence and respond within <strong>72 hours</strong>.</p>
          <a href="https://hypear.ai/disputes/{dispute_id}" style="background:#ef4444;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;">View Dispute</a>
        </div>
        """
    },
    "pii_violation": {
        "subject": "🚫 Personal information blocked in your message",
        "html": """
        <div style="font-family:Inter,sans-serif;max-width:600px;margin:auto;padding:32px;">
          <h1 style="color:#f59e0b;">Message Blocked</h1>
          <p>A recent message you sent contained personal contact information (phone number, email, or social handle).</p>
          <p>Hypear AI automatically removes this to protect both parties' anonymity.</p>
          <p><strong>Continued violations may result in account review.</strong></p>
          <p>To exchange contact info, both parties must sign an NDA first.</p>
        </div>
        """
    },
}


class NotificationService:
    """
    Dispatch push notifications (FCM) and emails (SendGrid).
    All methods gracefully degrade if API keys are not configured.
    """

    # ── FCM Push ─────────────────────────────────────────────

    @classmethod
    def push(cls, fcm_token: str, event: str, data: Dict[str, Any] = None) -> bool:
        """
        Send a push notification via Firebase FCM.
        Returns True on success, False on failure (graceful degradation).
        """
        if not fcm_token:
            return False
        if not _init_firebase():
            return False

        data = data or {}
        template = PUSH_TEMPLATES.get(event)
        if not template:
            logger.warning(f"No push template for event: {event}")
            return False

        try:
            from firebase_admin import messaging

            body = template["body"].format(**data)
            title = template["title"]

            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                token=fcm_token,
                data={"event": event, **{k: str(v) for k, v in data.items()}}
            )
            result = messaging.send(message)
            logger.info(f"FCM push sent [{event}]: {result}")
            return True

        except Exception as e:
            logger.error(f"FCM push failed for event '{event}': {e}")
            return False

    @classmethod
    def push_to_profile(cls, db, profile_id: str, event: str, data: Dict[str, Any] = None) -> bool:
        """Look up FCM token by profile ID and send push notification."""
        try:
            from server.db.models import Profile
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            if not profile or not profile.fcm_token:
                return False
            return cls.push(profile.fcm_token, event, data)
        except Exception as e:
            logger.error(f"push_to_profile failed: {e}")
            return False

    # ── SendGrid Email ────────────────────────────────────────

    @classmethod
    def email(cls, to: str, event: str, data: Dict[str, Any] = None) -> bool:
        """
        Send a transactional email via SendGrid.
        Returns True on success, False on failure.
        """
        api_key = os.environ.get("SENDGRID_API_KEY")
        if not api_key:
            logger.warning("SENDGRID_API_KEY not set — email disabled.")
            return False

        data = data or {}
        template = EMAIL_TEMPLATES.get(event)
        if not template:
            logger.warning(f"No email template for event: {event}")
            return False

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail

            subject = template["subject"]
            html = template["html"].format(**data)

            sg = sendgrid.SendGridAPIClient(api_key)
            mail = Mail(
                from_email="noreply@hypear.ai",
                to_emails=to,
                subject=subject,
                html_content=html
            )
            response = sg.send(mail)
            logger.info(f"Email sent [{event}] to {to}: status {response.status_code}")
            return response.status_code in (200, 202)

        except Exception as e:
            logger.error(f"SendGrid email failed for event '{event}': {e}")
            return False

    # ── Batch Notifications ───────────────────────────────────

    @classmethod
    def notify_both_parties(
        cls,
        db,
        project_id: str,
        event: str,
        data: Dict[str, Any] = None
    ):
        """Notify both brand and creator for a project event."""
        try:
            from server.db.models import Project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return

            data = data or {}
            data["project_id"] = project_id[:8]

            cls.push_to_profile(db, project.brand_id, event, data)
            cls.push_to_profile(db, project.creator_id, event, data)
        except Exception as e:
            logger.error(f"notify_both_parties failed: {e}")

    @classmethod
    def register_fcm_token(cls, db, profile_id: str, fcm_token: str):
        """Update the FCM token for a profile (called from client on app init)."""
        try:
            from server.db.models import Profile
            profile = db.query(Profile).filter(Profile.id == profile_id).first()
            if profile:
                profile.fcm_token = fcm_token
                db.commit()
                logger.debug(f"FCM token updated for {profile_id}")
        except Exception as e:
            logger.error(f"FCM token registration failed: {e}")
