"""
Creator-to-Creator Collaboration Engine for FRAME.
Conforms to Section 16 of the Master Specification:
- Co-production invitations
- Prevents duplicate invites and self-invitation
- Status progression: pending -> accepted / rejected -> completed
- Confirmed attribution before public display
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.db.models import Collaboration, Profile, AuditLog

class CollaborationService:
    @classmethod
    def invite_collaborator(
        cls,
        db: Session,
        initiator_id: str,
        invitee_id: str,
        project_id: Optional[str],
        roles: List[str],
        attribution_details: Optional[str]
    ) -> Collaboration:
        if initiator_id == invitee_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite yourself to collaborate.")

        invitee = db.query(Profile).filter(Profile.id == invitee_id).first()
        if not invitee or invitee.role != "creator":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitee creator not found.")

        # Check duplicate pending
        existing = db.query(Collaboration).filter(
            Collaboration.initiator_id == initiator_id,
            Collaboration.invitee_id == invitee_id,
            Collaboration.status == "pending"
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pending collaboration invitation already exists.")

        collab = Collaboration(
            project_id=project_id,
            initiator_id=initiator_id,
            invitee_id=invitee_id,
            status="pending",
            roles=json.dumps(roles),
            attribution_details=attribution_details
        )
        db.add(collab)
        db.commit()
        db.refresh(collab)

        # Audit log
        db.add(AuditLog(
            actor_id=initiator_id,
            action="INVITE_COLLABORATOR",
            resource_type="collaboration",
            resource_id=collab.id,
            metadata_json=json.dumps({"invitee_id": invitee_id, "roles": roles})
        ))
        db.commit()
        return collab

    @classmethod
    def respond_to_collaboration(
        cls,
        db: Session,
        invitee_id: str,
        collaboration_id: str,
        response_status: str # accepted, rejected, withdrawn
    ) -> Collaboration:
        collab = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
        if not collab:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaboration not found.")

        if response_status == "withdrawn":
            if collab.initiator_id != invitee_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only initiator can withdraw invitation.")
        else:
            if collab.invitee_id != invitee_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only invited creator can accept or reject.")

        if collab.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot respond: already in '{collab.status}' state.")

        collab.status = response_status
        db.commit()
        db.refresh(collab)

        # Audit log
        db.add(AuditLog(
            actor_id=invitee_id,
            action=f"COLLABORATION_{response_status.upper()}",
            resource_type="collaboration",
            resource_id=collab.id,
            metadata_json=json.dumps({"status": response_status})
        ))
        db.commit()
        return collab

    @classmethod
    def complete_collaboration(
        cls,
        db: Session,
        user_id: str,
        collaboration_id: str
    ) -> Collaboration:
        collab = db.query(Collaboration).filter(Collaboration.id == collaboration_id).first()
        if not collab:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collaboration not found.")
        if collab.initiator_id != user_id and collab.invitee_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized participant.")
        if collab.status != "accepted":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collaboration must be accepted before completing.")

        collab.status = "completed"
        db.commit()
        db.refresh(collab)
        return collab
