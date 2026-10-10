"""
Portfolio Publication Approval Router for FRAME.
Conforms to Section 14 of the Master Specification.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import PortfolioApprovalRequest, Profile
from server.services.portfolio_approval_service import PortfolioApprovalService
from server.services.auth_service import get_current_user

router = APIRouter(prefix="/api/approvals", tags=["Portfolio Approvals"])

class ApprovalCreateRequest(BaseModel):
    client_id: str
    project_id: str
    requested_media_scope: str
    requested_metadata_scope: str
    requested_platforms: List[str] = Field(default_factory=lambda: ["Instagram", "Portfolio"])
    embargo_until: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class ApprovalReviewRequest(BaseModel):
    decision: str # approved, rejected, changes_requested
    decision_notes: Optional[str] = None

class PublishApprovedRequest(BaseModel):
    title: str
    description: str
    content_type: str
    media_path: str
    thumbnail_path: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    style_tags: List[str] = Field(default_factory=list)
    ai_tools: List[str] = Field(default_factory=list)
    ai_models: List[str] = Field(default_factory=list)
    aspect_ratio: str = "16:9"

@router.post("/request")
def request_approval(
    req: ApprovalCreateRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Creator submits publication approval request for client project work."""
    record = PortfolioApprovalService.create_request(
        db=db,
        creator_id=current_user.id,
        client_id=req.client_id,
        project_id=req.project_id,
        requested_media_scope=req.requested_media_scope,
        requested_metadata_scope=req.requested_metadata_scope,
        requested_platforms=req.requested_platforms,
        embargo_until=req.embargo_until,
        expires_at=req.expires_at
    )
    return {"status": "submitted", "request_id": record.id}

@router.post("/{request_id}/review")
def review_approval(
    request_id: str,
    req: ApprovalReviewRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Client reviews, approves, or rejects the requested publication scope."""
    reviewed = PortfolioApprovalService.review_request(
        db=db,
        client_id=current_user.id,
        request_id=request_id,
        decision=req.decision,
        decision_notes=req.decision_notes
    )
    return {"status": reviewed.status, "request_id": reviewed.id}

@router.post("/{request_id}/publish")
def publish_approved(
    request_id: str,
    req: PublishApprovedRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Publishes the approved item publicly to creator portfolio."""
    item = PortfolioApprovalService.publish_approved_item(
        db=db,
        creator_id=current_user.id,
        request_id=request_id,
        title=req.title,
        description=req.description,
        content_type=req.content_type,
        media_path=req.media_path,
        thumbnail_path=req.thumbnail_path,
        skills=req.skills,
        style_tags=req.style_tags,
        ai_tools=req.ai_tools,
        ai_models=req.ai_models,
        aspect_ratio=req.aspect_ratio
    )
    return {"status": "published", "portfolio_item_id": item.id}

@router.post("/{request_id}/revoke")
def revoke_approval(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Client revokes previously granted publication approval."""
    revoked = PortfolioApprovalService.revoke_approval(
        db=db,
        client_id=current_user.id,
        request_id=request_id
    )
    return {"status": "revoked", "request_id": revoked.id}
