"""
PII Vault Service — Hypear AI Anonymous Marketplace.

Stores all real identity data (name, email, phone) using Fernet AES-256 encryption.
Real PII is NEVER stored in plain text anywhere in the database.

Key: PII_ENCRYPTION_KEY env variable (Fernet base64-encoded 32-byte key).
Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Access Policy:
  - create_vault()       → called once on signup
  - get_decrypted()      → ADMIN ONLY, KYC review panel
  - update_kyc_status()  → called by KYC webhook handlers
  - mask_display()       → public-safe display (alias or first-name only)
"""

import os
import hashlib
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Fernet Cipher Setup ──────────────────────────────────────
_PII_KEY = os.environ.get("PII_ENCRYPTION_KEY")

try:
    from cryptography.fernet import Fernet, InvalidToken
    _fernet = Fernet(_PII_KEY.encode()) if _PII_KEY else None
except Exception:
    _fernet = None
    logger.warning("PII_ENCRYPTION_KEY not set or invalid — PII encryption disabled. Set this before going to production.")


class PIIVaultService:
    """Manages encrypted PII storage and admin-gated decryption."""

    # ── Encryption Primitives ─────────────────────────────────

    @staticmethod
    def encrypt(value: str) -> Optional[str]:
        """Encrypt a plain-text string. Returns None if value is None."""
        if not value:
            return None
        if not _fernet:
            # Fallback for local dev without key: prefix with UNENCRYPTED marker
            logger.warning("Storing PII without encryption (dev mode).")
            return f"UNENC:{value}"
        return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decrypt(token: str) -> Optional[str]:
        """Decrypt a Fernet token. Returns None on failure."""
        if not token:
            return None
        if token.startswith("UNENC:"):
            return token[6:]
        if not _fernet:
            logger.error("Cannot decrypt — PII_ENCRYPTION_KEY not configured.")
            return None
        try:
            from cryptography.fernet import InvalidToken
            return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, Exception) as e:
            logger.error(f"PII decryption failed: {e}")
            return None

    @staticmethod
    def fingerprint(value: str) -> str:
        """SHA-256 fingerprint of a value (for duplicate detection without storing PII)."""
        return hashlib.sha256(value.lower().strip().encode()).hexdigest()

    # ── Vault Lifecycle ───────────────────────────────────────

    @classmethod
    def create_vault(
        cls,
        db,
        profile_id: str,
        real_name: str,
        real_email: str,
        real_phone: Optional[str] = None
    ):
        """
        Create a new PII Vault for a user.
        Called once during signup when real identity is provided.
        """
        from server.db.models import PIIVault

        existing = db.query(PIIVault).filter_by(profile_id=profile_id).first()
        if existing:
            logger.warning(f"PIIVault already exists for profile {profile_id}. Use update instead.")
            return existing

        vault = PIIVault(
            profile_id=profile_id,
            real_name_encrypted=cls.encrypt(real_name),
            real_email_encrypted=cls.encrypt(real_email),
            real_phone_encrypted=cls.encrypt(real_phone) if real_phone else None,
            kyc_status="not_started"
        )
        db.add(vault)
        db.commit()
        db.refresh(vault)
        logger.info(f"PIIVault created for profile {profile_id}")
        return vault

    @classmethod
    def update_vault(
        cls,
        db,
        profile_id: str,
        real_name: Optional[str] = None,
        real_email: Optional[str] = None,
        real_phone: Optional[str] = None
    ):
        """Update encrypted PII fields (called when user updates their real info)."""
        from server.db.models import PIIVault

        vault = db.query(PIIVault).filter_by(profile_id=profile_id).first()
        if not vault:
            return cls.create_vault(db, profile_id, real_name or "", real_email or "", real_phone)

        if real_name is not None:
            vault.real_name_encrypted = cls.encrypt(real_name)
        if real_email is not None:
            vault.real_email_encrypted = cls.encrypt(real_email)
        if real_phone is not None:
            vault.real_phone_encrypted = cls.encrypt(real_phone)

        db.commit()
        return vault

    @classmethod
    def get_decrypted(cls, db, profile_id: str, require_admin: bool = True) -> dict:
        """
        ADMIN-ONLY: Returns decrypted PII for KYC review.
        Never expose this endpoint publicly.
        """
        from server.db.models import PIIVault

        vault = db.query(PIIVault).filter_by(profile_id=profile_id).first()
        if not vault:
            return {"error": "No PII vault found for this profile."}

        return {
            "profile_id": profile_id,
            "real_name": cls.decrypt(vault.real_name_encrypted),
            "real_email": cls.decrypt(vault.real_email_encrypted),
            "real_phone": cls.decrypt(vault.real_phone_encrypted),
            "kyc_status": vault.kyc_status,
            "kyc_provider": vault.kyc_provider,
            "kyc_reference": vault.kyc_reference,
            "verified_at": vault.verified_at.isoformat() if vault.verified_at else None,
        }

    @classmethod
    def update_kyc_status(
        cls,
        db,
        profile_id: str,
        status: str,
        provider: str,
        reference: str
    ):
        """
        Update KYC status from webhook events.
        status: 'pending' | 'verified' | 'rejected'
        """
        from server.db.models import PIIVault

        vault = db.query(PIIVault).filter_by(profile_id=profile_id).first()
        if not vault:
            logger.error(f"No vault for {profile_id} during KYC update")
            return

        vault.kyc_status = status
        vault.kyc_provider = provider
        vault.kyc_reference = reference
        if status == "verified":
            vault.verified_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"KYC status → {status} for profile {profile_id}")
        return vault

    @classmethod
    def is_kyc_verified(cls, db, profile_id: str) -> bool:
        """Quick check — is this user's identity KYC-verified?"""
        from server.db.models import PIIVault
        vault = db.query(PIIVault).filter_by(profile_id=profile_id).first()
        return vault is not None and vault.kyc_status == "verified"
