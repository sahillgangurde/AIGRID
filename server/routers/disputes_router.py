"""
Dispute Resolution Router — Hypear AI v2.0.
/api/v2/disputes

Full dispute lifecycle management:
  - File a dispute (automatically freezes escrow)
  - Upload evidence (S3 stub — configure AWS_BUCKET_NAME)
  - Admin review and resolution
  - Escrow action on resolution (release/refund/split)

Dispute Reasons:
  non_delivery         → Creator didn't deliver on time
  quality_dispute      → Delivered work doesn't meet brief standards
  payment_issue        → Brand hasn't released approved milestone
  scope_creep          → Brand demanding work outside agreed brief
  identity_breach      → One party attempted to share/extract real identity

Resolution Actions (admin-only):
  release_to_creator   → Escrow goes to creator (creator was right)
  refund_to_brand      → Escrow refunded to brand (brand was right)
  split_50_50          → Equal split (compromise)
"""

import json
import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from server.db.session import get_db
from server.db.models import Dispute, Project, Profile, Transaction, AuditLog
from server.services.auth_service import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/disputes", tags=["Dispute Resolution"])

VALID_REASONS = (
    "non_delivery", "quality_dispute", "payment_issue",
    "scope_creep", "identity_breach", "other"
)

VALID_ESCROW_ACTIONS = (
    "release_to_creator", "refund_to_brand", "split_50_50"
)


# ── Pydantic Schemas ──────────────────────────────────────────

class FileDisputeRequest(BaseModel):
    project_id: str
    reason: str = Field(..., description=f"One of: {', '.join(VALID_REASONS)}")
    description: str = Field(..., min_length=20, max_length=2000)

class ResolveDisputeRequest(BaseModel):
    escrow_action: str = Field(..., description=f"One of: {', '.join(VALID_ESCROW_ACTIONS)}")
    resolution_notes: str = Field(..., min_length=10, max_length=2000)

class DisputeResponse(BaseModel):
    id: str
    project_id: str
    reason: str
    status: str
    description: str
    filed_at: str
    escrow_frozen: bool


# ── File a Dispute ────────────────────────────────────────────

@router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
def file_dispute(
    req: FileDisputeRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    File a new dispute for a project.
    Automatically freezes all pending escrow transactions for the project.
    """
    if req.reason not in VALID_REASONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid reason. Choose: {', '.join(VALID_REASONS)}"
        )

    # Validate project access
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    is_participant = (project.brand_id == current_user.id or
                      project.creator_id == current_user.id)
    if not is_participant:
        raise HTTPException(status_code=403, detail="You are not a participant in this project.")

    # Check for existing open dispute
    existing = db.query(Dispute).filter(
        Dispute.project_id == req.project_id,
        Dispute.status.in_(["open", "under_review"])
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An active dispute already exists for this project. Wait for resolution."
        )

    # Determine the other party
    against_id = (project.creator_id if current_user.id == project.brand_id
                  else project.brand_id)

    # Create dispute record
    dispute = Dispute(
        project_id=req.project_id,
        filed_by_id=current_user.id,
        against_id=against_id,
        reason=req.reason,
        description=req.description,
        evidence_urls="[]",
        status="open"
    )
    db.add(dispute)

    # Freeze project escrow — update all held transactions to 'disputed'
    frozen_count = 0
    transactions = db.query(Transaction).filter(
        Transaction.project_id == req.project_id,
        Transaction.status == "held_in_escrow"
    ).all()
    for txn in transactions:
        txn.status = "disputed"
        frozen_count += 1

    # Update project status
    project.status = "disputed"

    db.commit()
    db.refresh(dispute)

    # Audit log
    _log_audit(db, current_user.id, "dispute_filed", "dispute", dispute.id,
               {"project_id": req.project_id, "frozen_transactions": frozen_count})

    logger.info(f"Dispute {dispute.id} filed on project {req.project_id}. {frozen_count} transactions frozen.")

    return DisputeResponse(
        id=dispute.id,
        project_id=dispute.project_id,
        reason=dispute.reason,
        status=dispute.status,
        description=dispute.description,
        filed_at=dispute.created_at.isoformat(),
        escrow_frozen=frozen_count > 0
    )


# ── Upload Evidence ───────────────────────────────────────────

@router.post("/{dispute_id}/evidence")
async def upload_evidence(
    dispute_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Upload evidence files for an open dispute.
    Files are stored in S3 (configure AWS_BUCKET_NAME).
    Max 10 files, 50MB each.
    """
    dispute = _get_dispute_for_party(dispute_id, current_user.id, db)

    if dispute.status not in ("open", "under_review"):
        raise HTTPException(status_code=400, detail="Cannot add evidence to a resolved dispute.")

    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 evidence files per submission.")

    evidence_urls = json.loads(dispute.evidence_urls or "[]")
    uploaded = []

    for file in files:
        # Validate file size (50MB max)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File '{file.filename}' exceeds 50MB limit.")

        # In production: upload to S3
        # s3_url = await upload_to_s3(content, file.filename, f"disputes/{dispute_id}/")
        # For now: store filename as placeholder
        s3_url = f"https://s3.hypear.ai/disputes/{dispute_id}/{file.filename}"
        evidence_urls.append(s3_url)
        uploaded.append(file.filename)

    dispute.evidence_urls = json.dumps(evidence_urls)
    db.commit()

    return {
        "dispute_id": dispute_id,
        "uploaded_files": uploaded,
        "total_evidence": len(evidence_urls),
        "message": "Evidence uploaded successfully."
    }


# ── Get Dispute ───────────────────────────────────────────────

@router.get("/{dispute_id}")
def get_dispute(
    dispute_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Get dispute details. Parties can only see their own disputes."""
    dispute = _get_dispute_for_party(dispute_id, current_user.id, db)

    return {
        "id": dispute.id,
        "project_id": dispute.project_id,
        "reason": dispute.reason,
        "description": dispute.description,
        "status": dispute.status,
        "evidence_count": len(json.loads(dispute.evidence_urls or "[]")),
        "resolution_notes": dispute.resolution_notes if dispute.status not in ("open", "under_review") else None,
        "escrow_action": dispute.escrow_action,
        "filed_at": dispute.created_at.isoformat(),
        "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
    }


@router.get("/project/{project_id}")
def get_project_disputes(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Get all disputes for a project (participant access only)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    is_participant = (project.brand_id == current_user.id or
                      project.creator_id == current_user.id)
    if not is_participant and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    disputes = db.query(Dispute).filter(Dispute.project_id == project_id).all()
    return [{"id": d.id, "reason": d.reason, "status": d.status,
             "filed_at": d.created_at.isoformat()} for d in disputes]


# ── Admin Resolution ──────────────────────────────────────────

@router.post("/{dispute_id}/review")
def mark_under_review(
    dispute_id: str,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """Admin: Mark dispute as under review and assign self as arbitrator."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    dispute.status = "under_review"
    dispute.arbitrator_id = admin.id
    db.commit()

    return {"status": "under_review", "arbitrator_id": admin.id}


@router.post("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str,
    req: ResolveDisputeRequest,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """
    Admin-only: Resolve a dispute and trigger escrow action.
    This is irreversible — double-check before calling.
    """
    if req.escrow_action not in VALID_ESCROW_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid escrow action: {req.escrow_action}")

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    if dispute.status == "closed":
        raise HTTPException(status_code=400, detail="Dispute is already closed.")

    # Determine resolution status
    if req.escrow_action == "release_to_creator":
        dispute.status = "resolved_creator"
        _release_escrow_to_creator(dispute.project_id, db)
    elif req.escrow_action == "refund_to_brand":
        dispute.status = "resolved_brand"
        _refund_escrow_to_brand(dispute.project_id, db)
    elif req.escrow_action == "split_50_50":
        dispute.status = "resolved_brand"  # Both parties get partial
        _split_escrow(dispute.project_id, db)

    dispute.escrow_action = req.escrow_action
    dispute.resolution_notes = req.resolution_notes
    dispute.resolved_at = datetime.now(timezone.utc)
    dispute.arbitrator_id = admin.id

    # Update project status
    project = db.query(Project).filter(Project.id == dispute.project_id).first()
    if project:
        project.status = "delivered" if req.escrow_action == "release_to_creator" else "cancelled"

    db.commit()

    _log_audit(db, admin.id, "dispute_resolved", "dispute", dispute_id,
               {"action": req.escrow_action, "project_id": dispute.project_id})

    return {
        "dispute_id": dispute_id,
        "status": dispute.status,
        "escrow_action": req.escrow_action,
        "message": f"Dispute resolved. Escrow action: {req.escrow_action}"
    }


# ── Internal Helpers ──────────────────────────────────────────

def _get_dispute_for_party(dispute_id: str, user_id: str, db) -> Dispute:
    """Fetch dispute, enforcing that the user is a participant."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    # Check via project
    project = db.query(Project).filter(Project.id == dispute.project_id).first()
    if project:
        is_participant = (project.brand_id == user_id or project.creator_id == user_id)
        user = db.query(Profile).filter(Profile.id == user_id).first()
        is_admin = user and user.role == "admin"
        if not (is_participant or is_admin):
            raise HTTPException(status_code=403, detail="Access denied.")

    return dispute


def _release_escrow_to_creator(project_id: str, db):
    """Release all disputed transactions to creator."""
    transactions = db.query(Transaction).filter(
        Transaction.project_id == project_id,
        Transaction.status == "disputed"
    ).all()
    for txn in transactions:
        txn.status = "released"
    db.commit()


def _refund_escrow_to_brand(project_id: str, db):
    """Refund all disputed transactions to brand."""
    transactions = db.query(Transaction).filter(
        Transaction.project_id == project_id,
        Transaction.status == "disputed"
    ).all()
    for txn in transactions:
        txn.status = "refunded"
    db.commit()


def _split_escrow(project_id: str, db):
    """Mark transactions for 50/50 split (requires manual payout processing)."""
    transactions = db.query(Transaction).filter(
        Transaction.project_id == project_id,
        Transaction.status == "disputed"
    ).all()
    for txn in transactions:
        txn.status = "split_pending"
    db.commit()


def _log_audit(db, actor_id: str, action: str, resource_type: str, resource_id: str, meta: dict = None):
    try:
        entry = AuditLog(
            actor_id=actor_id, action=action,
            resource_type=resource_type, resource_id=resource_id,
            metadata_json=json.dumps(meta or {})
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


@router.post("/{dispute_id}/ai-audit")
def run_ai_dispute_audit(
    dispute_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Triggers autonomous LLM fact-finding & mediation agent for a dispute.
    Reconstructs objective timeline, detects scope creep, technical non-compliance,
    and returns fault percentage distribution with recommended escrow allocation.
    """
    from server.services.ai_dispute_agent import AIDisputeAgent

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    # Only participants or admin can run/view audit
    if current_user.role != "admin" and current_user.id != dispute.filed_by_id and current_user.id != dispute.against_id:
        raise HTTPException(status_code=403, detail="Unauthorized to audit this dispute.")

    try:
        report = AIDisputeAgent.audit_dispute(db=db, dispute_id=dispute_id)
        _log_audit(db, current_user.id, "ai_dispute_audited", "dispute", dispute_id, {"action": report["recommended_settlement"]["action"]})
        return {"status": "audited", "report": report}
    except Exception as e:
        logger.error(f"AI Dispute Audit failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI fact-finding failed: {e}")


@router.get("/{dispute_id}/ai-audit")
def get_ai_dispute_audit(
    dispute_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Retrieves existing AI fact-finding audit report or runs audit if not yet generated."""
    from server.services.ai_dispute_agent import AIDisputeAgent

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found.")

    if current_user.role != "admin" and current_user.id != dispute.filed_by_id and current_user.id != dispute.against_id:
        raise HTTPException(status_code=403, detail="Unauthorized to access this dispute audit.")

    if dispute.ai_audit_report:
        try:
            return {"status": "retrieved", "report": json.loads(dispute.ai_audit_report)}
        except Exception:
            pass

    # Run fresh audit if missing
    report = AIDisputeAgent.audit_dispute(db=db, dispute_id=dispute_id)
    return {"status": "freshly_audited", "report": report}

