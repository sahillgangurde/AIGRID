"""
Creator Collaborations Router for FRAME.
Conforms to Section 16 of the Master Specification.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Collaboration, Profile
from server.services.collaboration_service import CollaborationService
from server.services.auth_service import get_current_user

router = APIRouter(prefix="/api/collaborations", tags=["Collaborations"])

class InviteRequest(BaseModel):
    invitee_id: str
    project_id: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["Co-Director", "Neural VFX"])
    attribution_details: Optional[str] = None

class RespondRequest(BaseModel):
    response: str # accepted, rejected, withdrawn

@router.get("")
def list_user_collaborations(db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    """Lists collaborations involving current user."""
    collabs = db.query(Collaboration).filter(
        (Collaboration.initiator_id == current_user.id) | (Collaboration.invitee_id == current_user.id)
    ).all()
    return {"collaborations": collabs}

@router.post("/invite")
def invite_collaborator(
    req: InviteRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    collab = CollaborationService.invite_collaborator(
        db=db,
        initiator_id=current_user.id,
        invitee_id=req.invitee_id,
        project_id=req.project_id,
        roles=req.roles,
        attribution_details=req.attribution_details
    )
    return {"status": "invited", "collaboration_id": collab.id}

@router.post("/{collab_id}/respond")
def respond_collab(
    collab_id: str,
    req: RespondRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    collab = CollaborationService.respond_to_collaboration(
        db=db,
        invitee_id=current_user.id,
        collaboration_id=collab_id,
        response_status=req.response
    )
    return {"status": collab.status, "collaboration_id": collab.id}

@router.post("/{collab_id}/complete")
def complete_collab(
    collab_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    collab = CollaborationService.complete_collaboration(
        db=db,
        user_id=current_user.id,
        collaboration_id=collab_id
    )
    return {"status": "completed", "collaboration_id": collab.id}
