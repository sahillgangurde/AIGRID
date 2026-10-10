"""
Portfolio Publication Approval Engine for FRAME.
Conforms to Section 14 of the Master Specification:
- Scoped media & metadata approvals
- Enforces client authorization per project
- Re-validates embargo dates and expiration
- Prevents unapproved publishing bypass
- Full audit logging
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.db.models import PortfolioApprovalRequest, PortfolioItem, Project, AuditLog

class PortfolioApprovalService:
    @classmethod
    def create_request(
        cls,
        db: Session,
        creator_id: str,
        client_id: str,
        project_id: str,
        requested_media_scope: str,
        requested_metadata_scope: str,
        requested_platforms: List[str],
        embargo_until: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ) -> PortfolioApprovalRequest:
        # Validate that project exists and creator + client belong to it
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        if project.creator_id != creator_id or project.brand_id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participants do not match project.")

        req = PortfolioApprovalRequest(
            project_id=project_id,
            creator_id=creator_id,
            client_id=client_id,
            requested_media_scope=requested_media_scope,
            requested_metadata_scope=requested_metadata_scope,
            requested_platforms=json.dumps(requested_platforms),
            embargo_until=embargo_until,
            expires_at=expires_at,
            status="pending_approval"
        )
        db.add(req)
        db.commit()
        db.refresh(req)

        # Audit log
        db.add(AuditLog(
            actor_id=creator_id,
            action="CREATE_PORTFOLIO_APPROVAL_REQUEST",
            resource_type="portfolio_approval_request",
            resource_id=req.id,
            metadata_json=json.dumps({"project_id": project_id, "scope": requested_media_scope})
        ))
        db.commit()
        return req

    @classmethod
    def review_request(
        cls,
        db: Session,
        client_id: str,
        request_id: str,
        decision: str, # approved, rejected, changes_requested
        decision_notes: Optional[str] = None
    ) -> PortfolioApprovalRequest:
        req = db.query(PortfolioApprovalRequest).filter(PortfolioApprovalRequest.id == request_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")
        if req.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only authorized client can review this request.")

        if decision not in ('approved', 'rejected', 'changes_requested'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid decision status.")

        req.status = decision
        req.decision_notes = decision_notes
        req.decided_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(req)

        # Audit log
        db.add(AuditLog(
            actor_id=client_id,
            action=f"REVIEW_APPROVAL_{decision.upper()}",
            resource_type="portfolio_approval_request",
            resource_id=req.id,
            metadata_json=json.dumps({"decision": decision, "notes": decision_notes})
        ))
        db.commit()
        return req

    @classmethod
    def publish_approved_item(
        cls,
        db: Session,
        creator_id: str,
        request_id: str,
        title: str,
        description: str,
        content_type: str,
        media_path: str,
        thumbnail_path: Optional[str] = None,
        skills: List[str] = None,
        style_tags: List[str] = None,
        ai_tools: List[str] = None,
        ai_models: List[str] = None,
        aspect_ratio: str = "16:9"
    ) -> PortfolioItem:
        req = db.query(PortfolioApprovalRequest).filter(PortfolioApprovalRequest.id == request_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")
        if req.creator_id != creator_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized creator.")

        # Validate approved status
        if req.status != "approved":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot publish: request status is '{req.status}'.")

        now = datetime.now(timezone.utc)
        # Check embargo date
        if req.embargo_until:
            embargo_dt = req.embargo_until if req.embargo_until.tzinfo else req.embargo_until.replace(tzinfo=timezone.utc)
            if now < embargo_dt:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Item is under embargo until {req.embargo_until.isoformat()}.")

        # Check expiration date
        if req.expires_at:
            exp_dt = req.expires_at if req.expires_at.tzinfo else req.expires_at.replace(tzinfo=timezone.utc)
            if now > exp_dt:
                req.status = "expired"
                db.commit()
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Approval has expired.")

        # Create portfolio item
        item = PortfolioItem(
            creator_id=creator_id,
            title=title,
            description=description,
            content_type=content_type,
            media_path=media_path,
            thumbnail_path=thumbnail_path,
            skills=json.dumps(skills or []),
            style_tags=json.dumps(style_tags or []),
            ai_tools=json.dumps(ai_tools or []),
            ai_models=json.dumps(ai_models or []),
            aspect_ratio=aspect_ratio,
            visibility="public",
            rights_status="client_licensed",
            evidence_status="c2pa_signed",
            published_at=now
        )
        db.add(item)
        db.commit()
        db.refresh(item)

        req.portfolio_item_id = item.id
        db.commit()

        # Audit log
        db.add(AuditLog(
            actor_id=creator_id,
            action="PUBLISH_APPROVED_PORTFOLIO_ITEM",
            resource_type="portfolio_item",
            resource_id=item.id,
            metadata_json=json.dumps({"request_id": request_id, "title": title})
        ))
        db.commit()
        return item

    @classmethod
    def revoke_approval(cls, db: Session, client_id: str, request_id: str) -> PortfolioApprovalRequest:
        req = db.query(PortfolioApprovalRequest).filter(PortfolioApprovalRequest.id == request_id).first()
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found.")
        if req.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client can revoke approval.")

        req.status = "revoked"
        # If published, take down portfolio item visibility
        if req.portfolio_item_id:
            item = db.query(PortfolioItem).filter(PortfolioItem.id == req.portfolio_item_id).first()
            if item:
                item.visibility = "private"
        db.commit()
        db.refresh(req)

        # Audit log
        db.add(AuditLog(
            actor_id=client_id,
            action="REVOKE_PORTFOLIO_APPROVAL",
            resource_type="portfolio_approval_request",
            resource_id=req.id,
            metadata_json=json.dumps({"revoked_at": datetime.now(timezone.utc).isoformat()})
        ))
        db.commit()
        return req
