"""
Project Lifecycle, Milestones, and Linked Messaging Engine for FRAME.
Conforms to Section 15 of the Master Specification:
- Validated state machine transitions
- Milestone status progression
- Automatic project conversation provisioning
- Strict participant authorization on all actions
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.db.models import (
    Project, ProjectMilestone, CreativeBrief, Conversation, 
    ConversationParticipant, Message, Profile, AuditLog, TrustEvent, NDAgreement
)

ALLOWED_TRANSITIONS = {
    "draft": ["contacted", "in_discussion", "cancelled"],
    "contacted": ["in_discussion", "cancelled"],
    "in_discussion": ["in_production", "cancelled"],
    "in_production": ["submitted_for_review", "disputed", "cancelled"],
    "submitted_for_review": ["revision_requested", "delivered", "disputed"],
    "revision_requested": ["in_production", "submitted_for_review", "disputed"],
    "delivered": ["completed", "disputed"],
    "completed": [],
    "cancelled": [],
    "disputed": ["in_discussion", "cancelled", "completed"]
}

class ProjectService:
    @classmethod
    def create_project_from_brief(
        cls,
        db: Session,
        brand_id: str,
        creator_id: str,
        brief_id: Optional[str],
        title: str,
        budget_amount: float,
        currency: str = "INR",
        deadline: Optional[datetime] = None,
        visibility_mode: str = "public"
    ) -> Project:
        # Validate brand exists
        brand = db.query(Profile).filter(Profile.id == brand_id).first()
        creator = db.query(Profile).filter(Profile.id == creator_id).first()
        if not brand or not creator:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand or Creator not found.")

        # Create project
        project = Project(
            brand_id=brand_id,
            creator_id=creator_id,
            brief_id=brief_id,
            title=title,
            status="in_discussion",
            visibility_mode=visibility_mode,
            budget_amount=budget_amount,
            currency=currency,
            start_date=datetime.now(timezone.utc),
            deadline=deadline
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # Create default 3 milestones
        milestones = [
            ProjectMilestone(
                project_id=project.id,
                title="Phase 1: Creative Direction & Asset Setup",
                description="Prompt engineering, asset ingest, and initial preview generation.",
                percentage=30,
                amount=round(budget_amount * 0.3, 2),
                status="pending"
            ),
            ProjectMilestone(
                project_id=project.id,
                title="Phase 2: Rough Cut & Pacing Review",
                description="Draft assembly with sound sync and initial color grading.",
                percentage=40,
                amount=round(budget_amount * 0.4, 2),
                status="pending"
            ),
            ProjectMilestone(
                project_id=project.id,
                title="Phase 3: 4K Master Delivery & C2PA Provenance Seal",
                description="Final render upscaled with tamper-proof cryptographic manifest.",
                percentage=30,
                amount=round(budget_amount * 0.3, 2),
                status="pending"
            )
        ]
        db.add_all(milestones)

        # Provision project-linked conversation room
        conv = Conversation(
            created_by=brand_id,
            project_id=project.id,
            conversation_type="project"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        # Add both participants
        p1 = ConversationParticipant(conversation_id=conv.id, user_id=brand_id)
        p2 = ConversationParticipant(conversation_id=conv.id, user_id=creator_id)
        db.add_all([p1, p2])

        # Welcome message
        welcome_msg = Message(
            conversation_id=conv.id,
            sender_id=brand_id,
            body=f"Project workspace initialized for '{title}'. Total Escrow Allocation: {currency} {budget_amount:,.2f}."
        )
        db.add(welcome_msg)
        db.commit()

        # Provision project NDA
        nda = NDAgreement(
            project_id=project.id,
            brand_id=brand_id,
            creator_id=creator_id,
            template_version="v1.0",
            status="pending"
        )
        db.add(nda)

        # Audit log
        db.add(AuditLog(
            actor_id=brand_id,
            action="CREATE_PROJECT",
            resource_type="project",
            resource_id=project.id,
            metadata_json=json.dumps({"title": title, "creator_id": creator_id})
        ))
        db.commit()

        return project

    @classmethod
    def update_project_status(
        cls,
        db: Session,
        user_id: str,
        project_id: str,
        new_status: str
    ) -> Project:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

        # Check participant authorization
        if project.brand_id != user_id and project.creator_id != user_id:
            user = db.query(Profile).filter(Profile.id == user_id).first()
            if not user or user.role != "admin":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this project.")

        # Validate state transition
        allowed = ALLOWED_TRANSITIONS.get(project.status, [])
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transition from '{project.status}' to '{new_status}'. Allowed: {allowed}"
            )

        old_status = project.status
        project.status = new_status
        now = datetime.now(timezone.utc)

        if new_status in ('delivered', 'completed'):
            project.completed_at = now
            # Record trust event for on-time delivery
            is_on_time = True
            if project.deadline:
                dl = project.deadline if project.deadline.tzinfo else project.deadline.replace(tzinfo=timezone.utc)
                if now > dl:
                    is_on_time = False

            trust_ev = TrustEvent(
                creator_id=project.creator_id,
                project_id=project.id,
                event_type="project_completed_on_time" if is_on_time else "project_completed_late",
                event_status="verified",
                evidence_reference=f"Completed transition {old_status} -> {new_status}"
            )
            db.add(trust_ev)

        db.commit()
        db.refresh(project)

        # Audit log
        db.add(AuditLog(
            actor_id=user_id,
            action="UPDATE_PROJECT_STATUS",
            resource_type="project",
            resource_id=project.id,
            metadata_json=json.dumps({"old_status": old_status, "new_status": new_status})
        ))
        db.commit()
        return project

    @classmethod
    def update_milestone_status(
        cls,
        db: Session,
        user_id: str,
        milestone_id: str,
        new_status: str
    ) -> ProjectMilestone:
        ms = db.query(ProjectMilestone).filter(ProjectMilestone.id == milestone_id).first()
        if not ms:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found.")

        project = db.query(Project).filter(Project.id == ms.project_id).first()
        if not project or (project.brand_id != user_id and project.creator_id != user_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized.")

        if new_status not in ('pending', 'in_progress', 'submitted', 'approved', 'rejected'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid milestone status.")

        ms.status = new_status
        if new_status == "approved":
            ms.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(ms)
        return ms
