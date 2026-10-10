"""
Projects, Milestones, and Contract Lifecycle Router for FRAME.
Conforms to Section 15 of the Master Specification.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Project, ProjectMilestone, Profile, Conversation, AdvanceRequest
from server.services.project_service import ProjectService
from server.services.finance_service import FinanceService
from server.services.auth_service import get_current_user

router = APIRouter(prefix="/api/projects", tags=["Projects & Milestones"])

class CreateProjectRequest(BaseModel):
    creator_id: str
    brief_id: Optional[str] = None
    title: str
    budget_amount: float
    currency: Optional[str] = "INR"
    deadline: Optional[datetime] = None
    visibility_mode: Optional[str] = "public"

class UpdateStatusRequest(BaseModel):
    status: str

class UpdateMilestoneRequest(BaseModel):
    status: str

class AdvanceDepositRequest(BaseModel):
    advance_amount: Optional[float] = None   # defaults to project.advance_amount (markup amount)
    provider_reference: Optional[str] = None # Razorpay order/payment id once integrated

class QuoteRequest(BaseModel):
    creator_quote: float
    markup_percent: Optional[float] = 0.20

def serialize_project(p: Project, db: Session, include_sensitive: bool = False) -> Dict[str, Any]:
    brand = db.query(Profile).filter(Profile.id == p.brand_id).first()
    creator = db.query(Profile).filter(Profile.id == p.creator_id).first()
    milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == p.id).all()
    conv = db.query(Conversation).filter(Conversation.project_id == p.id).first()

    return {
        "id": p.id,
        "title": p.title,
        "brand_id": p.brand_id,
        "brand_name": brand.display_name if brand else "Brand",
        "creator_id": p.creator_id,
        "creator_name": creator.display_name if creator else "Creator",
        "creator_handle": f"@{creator.username}" if creator else "@creator",
        "brief_id": p.brief_id,
        "status": p.status,
        "visibility_mode": p.visibility_mode,
        "budget_amount": p.budget_amount,
        "currency": p.currency,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "deadline": p.deadline.isoformat() if p.deadline else None,
        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
        "conversation_id": conv.id if conv else None,
        "milestones": [
            {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "amount": m.amount,
                "percentage": m.percentage,
                "status": m.status,
                "completed_at": m.completed_at.isoformat() if m.completed_at else None
            }
            for m in milestones
        ],
        "escrow": {
            "creator_quote": p.creator_quote_amount if include_sensitive else None,
            "brand_payable": p.brand_payable_amount if include_sensitive else None,
            "advance_amount": p.advance_amount,
            "escrow_state": p.escrow_state,
            "advance_locked_at": p.advance_locked_at.isoformat() if p.advance_locked_at else None,
            "contact_unlocked_at": p.contact_unlocked_at.isoformat() if p.contact_unlocked_at else None
        }
    }

@router.get("")
def list_user_projects(db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    """Returns projects where user is either brand or creator."""
    if current_user.role == "admin":
        projects = db.query(Project).order_by(Project.created_at.desc()).all()
    else:
        projects = db.query(Project).filter(
            (Project.brand_id == current_user.id) | (Project.creator_id == current_user.id)
        ).order_by(Project.created_at.desc()).all()

    return {"projects": [serialize_project(p, db, include_sensitive=True) for p in projects]}

@router.get("/{project_id}")
def get_project_detail(project_id: str, db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    if current_user.role != "admin" and p.brand_id != current_user.id and p.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view this project.")

    return serialize_project(p, db, include_sensitive=True)

@router.post("")
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    """Creates a project and provisions milestones and conversation."""
    brand_id = current_user.id
    project = ProjectService.create_project_from_brief(
        db=db,
        brand_id=brand_id,
        creator_id=req.creator_id,
        brief_id=req.brief_id,
        title=req.title,
        budget_amount=req.budget_amount,
        currency=req.currency or "INR",
        deadline=req.deadline,
        visibility_mode=req.visibility_mode or "public"
    )
    return {"status": "created", "project": serialize_project(project, db, include_sensitive=True)}

@router.patch("/{project_id}/status")
def update_project_status(
    project_id: str,
    req: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Updates project status with server-side state machine validation."""
    updated = ProjectService.update_project_status(
        db=db,
        user_id=current_user.id,
        project_id=project_id,
        new_status=req.status
    )
    return {"status": "updated", "project": serialize_project(updated, db, include_sensitive=True)}

@router.post("/{project_id}/quote")
def set_creator_quote(
    project_id: str,
    req: QuoteRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Creator records their agreed take-home quote. Brand is shown only the
    markup-adjusted payable (creator_quote × (1 + markup_percent)). The creator's
    own number is never exposed to the brand and vice versa.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.id != p.creator_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the project's creator can record a quote.")
    if p.escrow_state != "pending_advance":
        raise HTTPException(status_code=409, detail="Quote can only be set before the advance deposit is locked.")
    if req.creator_quote <= 0:
        raise HTTPException(status_code=400, detail="Quote must be greater than zero.")

    pricing = FinanceService.calculate_brand_quote(req.creator_quote, req.markup_percent or 0.20)
    p.creator_quote_amount = pricing["creator_quote"]
    p.markup_percent = req.markup_percent or 0.20
    p.brand_payable_amount = pricing["brand_payable"]
    p.advance_amount = pricing["advance_deposit"]  # markup doubles as the advance deposit
    db.commit()

    return {
        "status": "quote_recorded",
        "brand_facing": {  # creator NEVER sees brand_payable; brand NEVER sees creator_quote
            "brand_payable": pricing["brand_payable"],
            "advance_deposit": pricing["advance_deposit"],
            "currency": p.currency
        }
    }

@router.post("/{project_id}/advance-deposit")
def lock_advance_deposit(
    project_id: str,
    req: AdvanceDepositRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Brand locks the advance deposit in escrow. On success:
      escrow_state → 'advance_locked', enabling contact reveal (post-NDA).
    This is the anti-disintermediation gate: no deposit → no identity reveal.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.id != p.brand_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the project's brand can pay the advance deposit.")
    if not req.advance_amount and not p.advance_amount:
        raise HTTPException(status_code=400, detail="No advance amount recorded. Creator must set a quote first.")

    tx = FinanceService.create_advance_deposit(
        db=db, project=p,
        advance_amount=req.advance_amount,
        provider_reference=req.provider_reference
    )

    # Wire: deal finalized → notify both parties + admin audit trail.
    try:
        from server.services.notification_service import NotificationService
        NotificationService.notify_both_parties(
            db, p.id, "deal_finalized",
            {"amount": tx.gross_amount, "currency": tx.currency}
        )
        approve_admins = db.query(Profile).filter(Profile.role == "admin").all()
        for admin in approve_admins:
            NotificationService.push_to_profile(
                db, admin.id, "deal_finalized",
                {"amount": tx.gross_amount, "currency": tx.currency}
            )
    except Exception:
        pass

    return {
        "status": "advance_locked",
        "transaction": {
            "id": tx.id,
            "amount": tx.gross_amount,
            "currency": tx.currency,
            "escrow_status": tx.status,
            "provider_reference": tx.provider_reference
        },
        "escrow_state": p.escrow_state,
        "message": "Advance locked in escrow. Contact can be unlocked after both parties sign the NDA."
    }


# ── Creator-Custom Advance Requests (flexible advance flow) ──

class AdvanceRequestCreate(BaseModel):
    amount: float
    reason: Optional[str] = None

class AdvanceRequestDecision(BaseModel):
    action: str  # approve | reject
    note: Optional[str] = None


@router.post("/{project_id}/advance-request")
def creator_requests_advance(
    project_id: str,
    req: AdvanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Creator requests a CUSTOM advance amount from the brand (with reason).
    Brand must approve; the approved amount becomes the escrow advance and
    replaces the fixed markup-derived advance.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.id != p.creator_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the project's creator can request a custom advance.")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Advance amount must be greater than zero.")
    if p.budget_amount and req.amount >= p.budget_amount:
        raise HTTPException(status_code=400, detail="Custom advance cannot meet or exceed the total project budget.")
    if p.escrow_state == "advance_locked":
        raise HTTPException(status_code=409, detail="Advance deposit is already locked for this project.")

    # Only one pending request per project — supersede older pending ones.
    pending = db.query(AdvanceRequest).filter(
        AdvanceRequest.project_id == project_id,
        AdvanceRequest.status == "pending"
    ).all()
    for old in pending:
        old.status = "superseded"

    ar = AdvanceRequest(
        project_id=project_id,
        creator_id=current_user.id,
        brand_id=p.brand_id,
        amount=round(req.amount, 2),
        currency=p.currency,
        reason=req.reason
    )
    db.add(ar)
    db.commit()
    db.refresh(ar)

    # Notify the brand that an advance request is awaiting approval.
    try:
        from server.services.notification_service import NotificationService
        NotificationService.push_to_profile(
            db, p.brand_id, "advance_requested",
            {"amount": ar.amount, "currency": ar.currency, "project_id": project_id[:8]}
        )
    except Exception:
        pass

    return {
        "status": "advance_requested",
        "request": {
            "id": ar.id,
            "project_id": ar.project_id,
            "amount": ar.amount,
            "currency": ar.currency,
            "reason": ar.reason,
            "status": ar.status
        }
    }


@router.post("/advance-requests/{request_id}/decision")
def brand_decides_advance(
    request_id: str,
    req: AdvanceRequestDecision,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Brand approves or rejects the creator's custom advance request.
    On approval → project.advance_amount is re-locked to the requested amount
    (brand-facing quote recomputed so brand_payable = creator_quote + requested advance).
    """
    ar = db.query(AdvanceRequest).filter(AdvanceRequest.id == request_id).first()
    if not ar:
        raise HTTPException(status_code=404, detail="Advance request not found.")
    p = db.query(Project).filter(Project.id == ar.project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.id != ar.brand_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the project's brand can decide on this advance request.")
    if ar.status != "pending":
        raise HTTPException(status_code=409, detail=f"Request already {ar.status}.")
    if req.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'.")

    ar.status = "approved" if req.action == "approve" else "rejected"
    ar.decided_at = datetime.now(timezone.utc)
    ar.decision_note = req.note

    if ar.status == "approved":
        # The approved advance replaces the fixed markup-derived advance.
        p.advance_amount = ar.amount
        if hasattr(p, "escrow_state") and p.escrow_state != "advance_locked":
            p.escrow_state = "pending_advance"

    db.commit()
    db.refresh(ar)

    return {
        "status": ar.status,
        "request": {
            "id": ar.id,
            "project_id": ar.project_id,
            "amount": ar.amount,
            "currency": ar.currency,
            "status": ar.status,
            "decision_note": ar.decision_note
        },
        "project_advance_amount": p.advance_amount,
        "escrow_state": p.escrow_state,
        "message": (
            "Advance request approved — brand can now lock this amount in escrow via /advance-deposit."
            if ar.status == "approved" else
            "Advance request rejected."
        )
    }


@router.get("/{project_id}/advance-requests")
def list_advance_requests(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Lists advance requests for a project (participants and admins only)."""
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.role != "admin" and p.brand_id != current_user.id and p.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized.")

    reqs = db.query(AdvanceRequest).filter(
        AdvanceRequest.project_id == project_id
    ).order_by(AdvanceRequest.created_at.desc()).all()

    return {
        "project_id": project_id,
        "requests": [
            {
                "id": r.id,
                "amount": r.amount,
                "currency": r.currency,
                "reason": r.reason,
                "status": r.status,
                "decision_note": r.decision_note,
                "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in reqs
        ]
    }

@router.patch("/{project_id}/milestones/{milestone_id}/status")
def update_milestone_status(
    project_id: str,
    milestone_id: str,
    req: UpdateMilestoneRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Updates a project milestone's status."""
    ms = ProjectService.update_milestone_status(
        db=db,
        user_id=current_user.id,
        milestone_id=milestone_id,
        new_status=req.status
    )
    return {"status": "updated", "milestone": {
        "id": ms.id,
        "title": ms.title,
        "status": ms.status,
        "completed_at": ms.completed_at.isoformat() if ms.completed_at else None
    }}


class SubmitDraftRequest(BaseModel):
    file_path: str
    title: Optional[str] = "Work-in-Progress Draft"
    milestone_id: Optional[str] = None


@router.post("/{project_id}/drafts")
def submit_project_draft(
    project_id: str,
    req: SubmitDraftRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """
    Creator submits a work-in-progress draft.
    Server applies dynamic semi-transparent review watermark before presenting to brand.
    """
    from server.services.watermark_service import WatermarkService

    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.id != p.creator_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only the project creator can submit drafts.")

    try:
        result = WatermarkService.process_draft_submission(
            db=db,
            project_id=project_id,
            creator_id=current_user.id,
            file_path=req.file_path,
            title=req.title,
            milestone_id=req.milestone_id
        )
        return {"status": "submitted_and_watermarked", "draft": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Watermark processing failed: {e}")


@router.get("/{project_id}/drafts")
def list_project_drafts(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Lists draft submissions for project with secure watermarked renditions."""
    from server.db.models import DraftSubmission

    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")
    if current_user.role != "admin" and p.brand_id != current_user.id and p.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to view drafts for this project.")

    drafts = db.query(DraftSubmission).filter(
        DraftSubmission.project_id == project_id
    ).order_by(DraftSubmission.submitted_at.desc()).all()

    is_creator = current_user.id == p.creator_id or current_user.role == "admin"
    results = []
    for d in drafts:
        results.append({
            "id": d.id,
            "title": d.title,
            "version": d.version,
            "file_type": d.file_type,
            "watermarked_file_path": d.watermarked_file_path,
            # Brand ONLY gets watermarked path unless project is completed_settled
            "original_file_path": d.original_file_path if (is_creator or p.status == "delivered") else None,
            "watermark_token": d.watermark_token,
            "c2pa_manifest_id": d.c2pa_manifest_id,
            "status": d.status,
            "submitted_at": d.submitted_at.isoformat() if d.submitted_at else None
        })

    return {"project_id": project_id, "drafts": results}

