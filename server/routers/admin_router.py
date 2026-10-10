"""
Administrative, Audit, and Moderation Router for FRAME.
Conforms to Sections 4, 19 of the Master Specification:
- Protected admin-only endpoints
- Platform audit logs inspection
- Content reports & moderation review
- Authorized genuine verification updates
"""

import json
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Report, AuditLog, Profile, VerificationRecord
from server.services.auth_service import get_current_user, require_admin

router = APIRouter(prefix="/api/admin", tags=["Administration & Audit"])

class CreateReportRequest(BaseModel):
    target_type: str # profile, post, brief, message
    target_id: str
    reason: str
    description: Optional[str] = None

class ResolveReportRequest(BaseModel):
    status: str # resolved, dismissed
    action_taken: Optional[str] = None

class UpdateVerificationRequest(BaseModel):
    user_id: str
    status: str # verified, failed, needs_review
    is_demo: bool = False
    provider_reference: Optional[str] = "ADMIN_MANUAL_VERIF"

@router.post("/reports")
def submit_report(
    req: CreateReportRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Submits a content or user violation report."""
    rep = Report(
        reporter_id=current_user.id,
        target_type=req.target_type,
        target_id=req.target_id,
        reason=req.reason,
        description=req.description,
        status="open"
    )
    db.add(rep)
    db.commit()
    db.refresh(rep)

    db.add(AuditLog(
        actor_id=current_user.id,
        action="SUBMIT_REPORT",
        resource_type="report",
        resource_id=rep.id,
        metadata_json=json.dumps({"target_type": req.target_type, "target_id": req.target_id})
    ))
    db.commit()
    return {"status": "submitted", "report_id": rep.id}

@router.get("/reports")
def list_reports(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """Lists moderation reports (admin only)."""
    q = db.query(Report)
    if status_filter:
        q = q.filter(Report.status == status_filter)
    reports = q.order_by(Report.created_at.desc()).all()
    return {"reports": reports}

@router.patch("/reports/{report_id}")
def resolve_report(
    report_id: str,
    req: ResolveReportRequest,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """Resolves or dismisses a report (admin only)."""
    rep = db.query(Report).filter(Report.id == report_id).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found.")

    rep.status = req.status
    rep.reviewed_by = admin.id
    rep.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    db.add(AuditLog(
        actor_id=admin.id,
        action=f"REPORT_{req.status.upper()}",
        resource_type="report",
        resource_id=rep.id,
        metadata_json=json.dumps({"action_taken": req.action_taken})
    ))
    db.commit()
    return {"status": "updated", "report": rep}

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """Retrieves immutable system audit logs (admin only)."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {
        "logs": [
            {
                "id": l.id,
                "actor_id": l.actor_id,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "metadata": json.loads(l.metadata_json or "{}"),
                "created_at": l.created_at.isoformat() if l.created_at else None
            }
            for l in logs
        ]
    }

@router.post("/verify-creator")
def admin_verify_creator(
    req: UpdateVerificationRequest,
    db: Session = Depends(get_db),
    admin: Profile = Depends(require_admin)
):
    """Updates genuine verification status through authorized admin workflow."""
    rec = db.query(VerificationRecord).filter(VerificationRecord.user_id == req.user_id).first()
    now = datetime.now(timezone.utc)
    if not rec:
        rec = VerificationRecord(
            user_id=req.user_id,
            verification_type="identity_kyc",
            provider_reference=req.provider_reference,
            status=req.status,
            is_demo=req.is_demo,
            verified_at=now if req.status == "verified" else None
        )
        db.add(rec)
    else:
        rec.status = req.status
        rec.is_demo = req.is_demo
        rec.provider_reference = req.provider_reference
        rec.verified_at = now if req.status == "verified" else None
        rec.last_updated_at = now

    db.commit()

    db.add(AuditLog(
        actor_id=admin.id,
        action="UPDATE_USER_VERIFICATION",
        resource_type="verification_record",
        resource_id=rec.id,
        metadata_json=json.dumps({"user_id": req.user_id, "status": req.status, "is_demo": req.is_demo})
    ))
    db.commit()
    return {"status": "success", "verification_status": rec.status, "is_demo": rec.is_demo}
