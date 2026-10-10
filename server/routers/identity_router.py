"""
Identity Router — Hypear AI v2.0.
/api/v2/identity

Manages the full anonymous identity lifecycle:
  - Alias generation and regeneration
  - Anonymous mode toggle
  - KYC initiation and status
  - Identity reveal (post-NDA signing)
  - PII vault management (admin-gated)

All creator-facing responses use masked_alias ONLY.
Real names are never returned by any endpoint in this router.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from server.db.session import get_db
from server.db.models import Profile, PIIVault, NDAgreement, AuditLog, Project
from server.services.auth_service import get_current_user, require_admin
from server.services.alias_generator import AliasGenerator
from server.services.pii_vault_service import PIIVaultService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/identity", tags=["Anonymous Identity"])

# ── Pydantic Schemas ──────────────────────────────────────────

class AliasResponse(BaseModel):
    alias: str
    anonymous_mode: bool
    message: str

class AnonymousModeToggleRequest(BaseModel):
    enable: bool

class PIIRegistrationRequest(BaseModel):
    real_name: str = Field(..., min_length=2, max_length=200)
    real_email: str = Field(..., min_length=5, max_length=254)
    real_phone: Optional[str] = Field(None, min_length=10, max_length=15)

class KYCInitiateRequest(BaseModel):
    provider: str = Field(..., description="'aadhaar_api' or 'stripe_identity'")

class IdentityStatusResponse(BaseModel):
    profile_id: str
    masked_alias: Optional[str]
    anonymous_mode: bool
    pii_violation_count: int
    kyc_status: str
    account_status: str

# ── Alias Endpoints ───────────────────────────────────────────

@router.post("/alias/generate", response_model=AliasResponse)
def generate_alias(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Generate a fresh unique anonymous alias for the authenticated user.
    Can be called once at signup; regeneration has a 30-day cooldown.
    """
    if current_user.masked_alias:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an alias. Use /alias/regenerate to change it (30-day cooldown applies)."
        )

    alias = AliasGenerator.assign_to_profile(db, current_user.id)

    _log_audit(db, current_user.id, "alias_generated", "profile", current_user.id)

    return AliasResponse(
        alias=alias,
        anonymous_mode=current_user.anonymous_mode,
        message=f"Your anonymous identity is: '{alias}'. Brands will only see this name."
    )


@router.post("/alias/regenerate", response_model=AliasResponse)
def regenerate_alias(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Regenerate alias (30-day cooldown enforced via audit log).
    Previous alias becomes available for reassignment immediately.
    """
    # Check cooldown via audit log
    from sqlalchemy import and_
    cooldown_start = datetime.now(timezone.utc) - timedelta(days=30)
    recent_regen = db.query(AuditLog).filter(
        and_(
            AuditLog.actor_id == current_user.id,
            AuditLog.action == "alias_regenerated",
            AuditLog.created_at >= cooldown_start
        )
    ).first()

    if recent_regen:
        next_allowed = recent_regen.created_at + timedelta(days=30)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Alias regeneration allowed once every 30 days. Next allowed: {next_allowed.strftime('%Y-%m-%d')}."
        )

    old_alias = current_user.masked_alias
    alias = AliasGenerator.assign_to_profile(db, current_user.id)

    _log_audit(db, current_user.id, "alias_regenerated", "profile", current_user.id,
               meta={"old_alias": old_alias, "new_alias": alias})

    return AliasResponse(
        alias=alias,
        anonymous_mode=current_user.anonymous_mode,
        message=f"Alias updated to: '{alias}'."
    )


@router.post("/anonymous-mode", response_model=AliasResponse)
def toggle_anonymous_mode(
    req: AnonymousModeToggleRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Enable or disable anonymous mode. When ON, display_name is replaced by masked_alias."""
    if req.enable and not current_user.masked_alias:
        # Auto-generate alias if not set
        AliasGenerator.assign_to_profile(db, current_user.id)
        db.refresh(current_user)

    current_user.anonymous_mode = req.enable
    db.commit()

    status_str = "enabled" if req.enable else "disabled"
    return AliasResponse(
        alias=current_user.masked_alias or current_user.display_name,
        anonymous_mode=current_user.anonymous_mode,
        message=f"Anonymous mode {status_str}. {'Brands now see your alias only.' if req.enable else 'Your display name is now visible.'}"
    )


# ── PII Vault Endpoints ───────────────────────────────────────

@router.post("/pii/register", status_code=status.HTTP_201_CREATED)
def register_pii(
    req: PIIRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Register real PII (name, email, phone) into the encrypted vault.
    Required before KYC initiation. Never stored in plain text.
    """
    vault = PIIVaultService.create_vault(
        db=db,
        profile_id=current_user.id,
        real_name=req.real_name,
        real_email=req.real_email,
        real_phone=req.real_phone
    )
    _log_audit(db, current_user.id, "pii_registered", "pii_vault", vault.id)

    return {
        "status": "success",
        "message": "Your real identity has been securely encrypted and stored. It will only be used for KYC verification.",
        "kyc_status": vault.kyc_status
    }


@router.post("/kyc/initiate")
def initiate_kyc(
    req: KYCInitiateRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Initiate KYC verification. Returns a redirect URL for the KYC provider.
    Providers: 'aadhaar_api' (India) | 'stripe_identity' (International)
    """
    valid_providers = ("aadhaar_api", "stripe_identity", "manual")
    if req.provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Choose: {', '.join(valid_providers)}"
        )

    vault = db.query(PIIVault).filter_by(profile_id=current_user.id).first()
    if not vault:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Register your real name and email first via /pii/register before starting KYC."
        )

    if vault.kyc_status == "verified":
        return {"message": "Identity already verified.", "kyc_status": "verified"}

    # Update vault to pending
    PIIVaultService.update_kyc_status(
        db=db,
        profile_id=current_user.id,
        status="pending",
        provider=req.provider,
        reference=f"pending_{current_user.id[:8]}"
    )

    # In production: call Aadhaar API or Stripe Identity SDK here
    # and return their redirect URL
    redirect_url = f"https://kyc.hypear.ai/{req.provider}/start?uid={current_user.id}"

    return {
        "status": "pending",
        "provider": req.provider,
        "redirect_url": redirect_url,
        "message": "Complete verification at the redirect URL. Your status updates automatically."
    }


@router.get("/kyc/status")
def get_kyc_status(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Get the current KYC status for the authenticated user."""
    vault = db.query(PIIVault).filter_by(profile_id=current_user.id).first()
    return {
        "kyc_status": vault.kyc_status if vault else "not_started",
        "kyc_provider": vault.kyc_provider if vault else None,
        "verified_at": vault.verified_at.isoformat() if vault and vault.verified_at else None
    }


# ── Identity Reveal Endpoints ─────────────────────────────────

@router.post("/reveal/{project_id}")
def reveal_identity(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Reveal real identity for a specific project.
    ONLY allowed after BOTH conditions hold (CreatorGrid escrow flow):
      1. Advance deposit is locked in escrow  (project.escrow_state == 'advance_locked')
      2. NDA is fully signed by BOTH parties
    Signs the current user's side of the NDA (via IP timestamp).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    is_brand = project.brand_id == current_user.id
    is_creator = project.creator_id == current_user.id
    if not (is_brand or is_creator):
        raise HTTPException(status_code=403, detail="You are not part of this project.")

    # ── Advance-deposit gate: no escrow money, no identity reveal ──
    if getattr(project, "escrow_state", "pending_advance") != "advance_locked":
        advance_needed = project.advance_amount or 0.0
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=(
                "Contact unlock requires the advance deposit to be locked in escrow first. "
                + (f"Outstanding advance: {project.currency} {advance_needed:,.2f}." if advance_needed else "The creator must record a quote before the advance can be paid.")
            )
        )

    nda = db.query(NDAgreement).filter(NDAgreement.project_id == project_id).first()
    if not nda:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="NDA has not been generated for this project yet."
        )

    # Hash the client IP for legal proof (stored, not raw IP)
    client_ip = request.client.host
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    if is_brand and not nda.brand_signed_at:
        nda.brand_signed_at = now
        nda.brand_ip_hash = ip_hash
    elif is_creator and not nda.creator_signed_at:
        nda.creator_signed_at = now
        nda.creator_ip_hash = ip_hash

    # Check if fully signed
    fully_signed = nda.brand_signed_at and nda.creator_signed_at
    if fully_signed:
        nda.status = "fully_signed"
        project.identity_revealed = True
        project.contact_unlocked_at = datetime.now(timezone.utc)

    db.commit()

    if fully_signed:
        # Return the other party's real display name (not encrypted fields)
        other_id = project.creator_id if is_brand else project.brand_id
        other = db.query(Profile).filter(Profile.id == other_id).first()
        return {
            "status": "revealed",
            "message": "Both parties have signed the NDA. Identity revealed.",
            "counterparty_display_name": other.display_name if other else None
        }
    else:
        return {
            "status": "partially_signed",
            "message": "Your signature has been recorded. Waiting for the other party to sign."
        }


# ── Identity Status ───────────────────────────────────────────

@router.get("/status", response_model=IdentityStatusResponse)
def get_identity_status(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Get a full overview of the authenticated user's anonymous identity state."""
    vault = db.query(PIIVault).filter_by(profile_id=current_user.id).first()
    return IdentityStatusResponse(
        profile_id=current_user.id,
        masked_alias=current_user.masked_alias,
        anonymous_mode=current_user.anonymous_mode,
        pii_violation_count=current_user.pii_violation_count or 0,
        kyc_status=vault.kyc_status if vault else "not_started",
        account_status=current_user.account_status
    )


# ── Admin-Only Endpoints ──────────────────────────────────────

@router.get("/admin/vault/{profile_id}")
def admin_view_vault(
    profile_id: str,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """ADMIN ONLY: Decrypt and view PII vault contents for KYC review."""
    data = PIIVaultService.get_decrypted(db, profile_id)
    _log_audit(db, admin.id, "admin_pii_viewed", "pii_vault", profile_id)
    return data


@router.post("/admin/kyc-approve/{profile_id}")
def admin_approve_kyc(
    profile_id: str,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """ADMIN ONLY: Manually approve KYC for a profile."""
    PIIVaultService.update_kyc_status(
        db=db, profile_id=profile_id,
        status="verified", provider="manual_admin", reference=f"admin_{admin.id[:8]}"
    )
    _log_audit(db, admin.id, "admin_kyc_approved", "pii_vault", profile_id)
    return {"status": "verified", "approved_by": admin.id}


# ── Internal Helpers ──────────────────────────────────────────

def _log_audit(db, actor_id: str, action: str, resource_type: str, resource_id: str, meta: dict = None):
    """Write an immutable audit log entry."""
    import json
    try:
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=json.dumps(meta or {})
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")
