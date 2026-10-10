"""
Conversations and Universal Messaging Router for FRAME.
Conforms to Section 15 of the Master Specification:
- Scoped to conversation participants
- Sender authorization derived strictly from session
- Project-linked conversation retrieval
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Conversation, ConversationParticipant, Message, Profile, Project
from server.services.auth_service import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["Messaging"])

class SendMessageRequest(BaseModel):
    body: str
    attachment_reference: Optional[str] = None

@router.get("")
def list_conversations(db: Session = Depends(get_db), current_user: Profile = Depends(get_current_user)):
    """Lists all conversations for the authenticated user."""
    participants = db.query(ConversationParticipant).filter(
        ConversationParticipant.user_id == current_user.id
    ).all()
    conv_ids = [p.conversation_id for p in participants]

    convs = db.query(Conversation).filter(Conversation.id.in_(conv_ids)).order_by(Conversation.updated_at.desc()).all()

    results = []
    for c in convs:
        # Get project title if linked
        project_title = None
        if c.project_id:
            proj = db.query(Project).filter(Project.id == c.project_id).first()
            if proj:
                project_title = proj.title

        # Last message
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()

        results.append({
            "id": c.id,
            "project_id": c.project_id,
            "project_title": project_title,
            "conversation_type": c.conversation_type,
            "last_message": {
                "body": last_msg.body,
                "sender_id": last_msg.sender_id,
                "created_at": last_msg.created_at.isoformat() if last_msg.created_at else None
            } if last_msg else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })

    return {"conversations": results}

@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Retrieves message history. Enforces participant authorization."""
    is_part = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    ).first()
    if not is_part and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this conversation.")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.deleted_at == None
    ).order_by(Message.created_at.asc()).all()

    # Update last read
    if is_part:
        is_part.last_read_at = datetime.now(timezone.utc)
        db.commit()

    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": (
                    m.sender.masked_alias if (m.sender and m.sender.anonymous_mode and m.sender.masked_alias)
                    else (m.sender.display_name if m.sender else "User")
                ),
                "sender_avatar": m.sender.avatar_url if m.sender else None,
                "is_anonymous": bool(m.sender and m.sender.anonymous_mode),
                "body": m.body,
                "attachment_reference": m.attachment_reference,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in messages
        ]
    }

@router.post("/{conversation_id}/messages")
def send_message(
    conversation_id: str,
    req: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Sends a message to the conversation with sender verification and PII interception."""
    from server.middleware.pii_interceptor import PIIInterceptorMiddleware

    is_part = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    ).first()
    if not is_part:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to send messages here.")

    # 1. Real-time PII Interception
    scan_result = PIIInterceptorMiddleware.scan_and_redact(req.body)
    if scan_result["has_pii"]:
        PIIInterceptorMiddleware.log_violation_to_db(
            db=db,
            user_id=current_user.id,
            channel_type="rest_chat",
            scan_result=scan_result
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PII_INTERCEPTED",
                "message": "Direct contact details or off-platform communication handles are prohibited.",
                "violations": scan_result["violations"],
                "redacted_preview": scan_result["redacted_text"],
                "violation_count": current_user.pii_violation_count,
                "strikes_remaining": max(0, 7 - current_user.pii_violation_count)
            }
        )

    msg = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        body=req.body,
        attachment_reference=req.attachment_reference
    )
    db.add(msg)

    # Update conversation updated_at
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conv:
        conv.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(msg)

    effective_name = (
        current_user.masked_alias if (current_user.anonymous_mode and current_user.masked_alias)
        else current_user.display_name
    )

    return {
        "status": "sent",
        "message": {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_name": effective_name,
            "body": msg.body,
            "attachment_reference": msg.attachment_reference,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
    }
