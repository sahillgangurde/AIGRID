"""
PII Interception Middleware — Hypear AI v2.0.

Scans ALL outbound chat messages for personal identity information before
they are stored in the database or delivered to recipients.

What it blocks:
  - Indian mobile numbers (10-digit, starting 6-9)
  - International phone numbers (+XX format)
  - Email addresses (any RFC 5322-compliant address)
  - Instagram / Twitter / X handles (@username)
  - WhatsApp / Telegram / LinkedIn hints (keywords)
  - UPI IDs (name@upihandle format)
  - Bank account-style strings

Security Design:
  - Detected PII is REPLACED with a redaction tag, never stored
  - SHA-256 hash of detected value stored in pii_intercept_events (for analytics, NOT recovery)
  - 3rd violation → account_status = 'pending_review'
  - 5th violation → account_status = 'suspended' (configurable)

Usage:
    from server.middleware.pii_interceptor import PIIInterceptor
    safe_text, was_blocked, violations = PIIInterceptor.scan_and_enforce(
        text=message_body,
        sender_id=current_user.id,
        db=db
    )
"""

import re
import hashlib
import logging
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)

# ── PII Detection Pattern Registry ───────────────────────────
#    Order matters: more specific patterns first.

PII_PATTERNS: Dict[str, str] = {
    # Phone numbers
    "phone_india":      r'\b[6-9]\d{9}\b',
    "phone_intl":       r'(?<!\d)\+\d{1,3}[\s\-\.]?\(?\d{1,4}\)?[\s\-\.]?\d{1,4}[\s\-\.]?\d{1,9}\b|\b[1-5]\d{9}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
    "phone_spaced":     r'\b(?:\d[\s\-\.]){9}\d\b',

    # Email addresses
    "email":            r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b',

    # UPI IDs (must come before generic email to handle overlaps)
    "upi_id":           r'\b[a-zA-Z0-9._\-]{3,256}@(?:upi|paytm|phonepe|gpay|okaxis|okhdfcbank|ybl|ibl|oksbi|okicici)\b',

    # Social handles
    "social_handle":    r'(?<!\w)@[a-zA-Z0-9_.]{3,30}\b',

    # Platform keywords (catch bypass attempts like "contact me on whatsapp")
    "whatsapp_hint":    r'\b(?:whatsapp|whts\s?app|wa\.me|whatsapp\.com)\b',
    "telegram_hint":    r'\b(?:telegram|t\.me|tele\s?gram)\b',
    "linkedin_hint":    r'\b(?:linkedin\.com|linked\s?in)\b',

    # Bypass attempt keywords
    "contact_bypass":   r'\b(?:my number|call me|text me|ping me on|reach me at|dm me|direct message me)\b',

    # Pre-quote price negotiation — final amounts must be set via the private
    # quote endpoint, NOT negotiated in chat (keeps the brand-payable masking
    # and the 20% markup intact). Blocks ₹/rs/paise amounts ≥ ₹1,000.
    "price_negotiation": r'(?:₹|rs\.?\s?|inr\s?)\s?\d[\d,]{3,}(?:\.\d{1,2})?\b',
}

REDACT_TAGS = {
    "phone_india":      "📵 [Phone Blocked]",
    "phone_intl":       "📵 [Phone Blocked]",
    "phone_spaced":     "📵 [Phone Blocked]",
    "email":            "✉️ [Email Blocked]",
    "upi_id":           "💳 [UPI Blocked]",
    "social_handle":    "🔒 [Handle Blocked]",
    "whatsapp_hint":    "🚫 [WhatsApp Ref Blocked]",
    "telegram_hint":    "🚫 [Telegram Ref Blocked]",
    "linkedin_hint":    "🚫 [LinkedIn Ref Blocked]",
    "contact_bypass":   "⚠️ [Contact Attempt Blocked]",
    "price_negotiation": "💰 [Quote Blocked — use the Quote endpoint]",
}

# Violation thresholds
REVIEW_THRESHOLD = 3
SUSPEND_THRESHOLD = 7


class PIIInterceptor:
    """
    Core PII scanning and enforcement engine.
    All methods are stateless — pass db session for persistence.
    """

    @staticmethod
    def scan(text: str) -> Tuple[bool, str, List[Dict]]:
        """
        Pure scan: no DB side effects.
        Returns:
            has_pii (bool): True if any PII was detected
            cleaned_text (str): text with PII replaced by redaction tags
            violations (list): [{type, hash, original_length}]
        """
        if not text or not text.strip():
            return False, text, []

        violations = []
        cleaned = text

        for pii_type, pattern in PII_PATTERNS.items():
            try:
                matches = re.findall(pattern, cleaned, re.IGNORECASE)
                for match in matches:
                    match_str = match if isinstance(match, str) else match[0]
                    # Hash the matched value (never store the raw value)
                    match_hash = hashlib.sha256(match_str.lower().strip().encode()).hexdigest()

                    violations.append({
                        "type": pii_type,
                        "hash": match_hash,
                        "original_length": len(match_str)
                    })

                    # Replace in text
                    tag = REDACT_TAGS.get(pii_type, "🚫 [Blocked]")
                    cleaned = re.sub(
                        re.escape(match_str),
                        tag,
                        cleaned,
                        count=1,
                        flags=re.IGNORECASE
                    )

            except re.error as e:
                logger.error(f"Regex error in PII pattern '{pii_type}': {e}")
                continue

        has_pii = len(violations) > 0
        return has_pii, cleaned, violations

    @classmethod
    def scan_and_enforce(
        cls,
        text: str,
        sender_id: str,
        db,
        conversation_id: str = None,
        message_id: str = None
    ) -> Tuple[str, bool, List[Dict]]:
        """
        Full enforcement pipeline:
          1. Scan for PII
          2. If found → log to pii_intercept_events
          3. Increment sender's violation counter
          4. Apply account review/suspension if threshold crossed
          5. Return cleaned text

        Returns:
            safe_text (str): redacted message body
            was_blocked (bool): True if any PII was found and removed
            violations (list): violation metadata
        """
        has_pii, cleaned_text, violations = cls.scan(text)

        if has_pii:
            cls._persist_violations(
                db=db,
                sender_id=sender_id,
                violations=violations,
                message_id=message_id,
                conversation_id=conversation_id
            )
            cls._enforce_policy(db=db, sender_id=sender_id, violation_count=len(violations))

        return cleaned_text, has_pii, violations

    @staticmethod
    def _persist_violations(db, sender_id: str, violations: List[Dict],
                             message_id: str = None, conversation_id: str = None):
        """Log each violation to pii_intercept_events table."""
        try:
            from server.db.models import PIIInterceptEvent

            for v in violations:
                event = PIIInterceptEvent(
                    sender_id=sender_id,
                    message_id=message_id,
                    conversation_id=conversation_id,
                    pii_type=v["type"],
                    was_blocked=True,
                    raw_match_hash=v["hash"]
                )
                db.add(event)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to persist PII violation events: {e}")
            db.rollback()

    @staticmethod
    def _enforce_policy(db, sender_id: str, violation_count: int):
        """Apply account-level consequences based on cumulative violation count."""
        try:
            from server.db.models import Profile

            user = db.query(Profile).filter(Profile.id == sender_id).first()
            if not user:
                return

            user.pii_violation_count = (user.pii_violation_count or 0) + violation_count

            if user.pii_violation_count >= SUSPEND_THRESHOLD:
                if user.account_status not in ("suspended",):
                    user.account_status = "suspended"
                    logger.warning(f"Account SUSPENDED due to PII violations: {sender_id}")

            elif user.pii_violation_count >= REVIEW_THRESHOLD:
                if user.account_status == "active":
                    user.account_status = "pending_review"
                    logger.warning(f"Account set to pending_review (PII violations): {sender_id}")

            db.commit()
        except Exception as e:
            logger.error(f"Failed to enforce PII policy for {sender_id}: {e}")
            db.rollback()

    @staticmethod
    def get_violation_summary(db, sender_id: str) -> Dict:
        """Return a summary of PII violations for a given user (admin use)."""
        try:
            from server.db.models import PIIInterceptEvent, Profile
            from sqlalchemy import func

            profile = db.query(Profile).filter(Profile.id == sender_id).first()
            total = db.query(func.count(PIIInterceptEvent.id))\
                       .filter(PIIInterceptEvent.sender_id == sender_id)\
                       .scalar()

            by_type = db.query(
                PIIInterceptEvent.pii_type,
                func.count(PIIInterceptEvent.id).label("count")
            ).filter(PIIInterceptEvent.sender_id == sender_id)\
             .group_by(PIIInterceptEvent.pii_type).all()

            return {
                "sender_id": sender_id,
                "total_violations": total,
                "cumulative_count_on_profile": profile.pii_violation_count if profile else 0,
                "account_status": profile.account_status if profile else "unknown",
                "by_type": {row.pii_type: row.count for row in by_type}
            }
        except Exception as e:
            logger.error(f"Failed to get violation summary: {e}")
            return {"error": str(e)}

    @classmethod
    def scan_and_redact(cls, text: str) -> Dict:
        """Convenience method returning a standardized dictionary result."""
        has_pii, cleaned_text, violations = cls.scan(text)
        return {
            "has_pii": has_pii,
            "redacted_text": cleaned_text,
            "violations": violations
        }

    @classmethod
    def log_violation_to_db(cls, db, user_id: str, channel_type: str, scan_result: Dict):
        """Log detected violation and enforce account thresholds."""
        from server.db.models import Conversation
        # Ensure conversation_id actually exists in conversations table before setting FK
        conv_id = None
        if channel_type and channel_type not in ("rest_chat", "socketio_chat"):
            c = db.query(Conversation).filter(Conversation.id == channel_type).first()
            if c:
                conv_id = c.id

        cls._persist_violations(
            db=db,
            sender_id=user_id,
            violations=scan_result.get("violations", []),
            conversation_id=conv_id
        )
        cls._enforce_policy(db=db, sender_id=user_id, violation_count=len(scan_result.get("violations", [])))


PIIInterceptorMiddleware = PIIInterceptor
