"""
Socket.IO ASGI Server with Integrated Real-Time PII Interception for Hypear AI.
Provides instantaneous detection and blocking of phone numbers, emails, UPI IDs,
social handles, and off-platform solicitation.
"""

import json
import logging
from datetime import datetime, timezone
import socketio
from sqlalchemy.orm import Session

from server.db.session import SessionLocal
import server.db.models as models
from server.middleware.pii_interceptor import PIIInterceptorMiddleware
from server.services.alias_generator import AliasGeneratorService
from server.services.notification_service import NotificationService

logger = logging.getLogger("hypear.socketio")

# Create asynchronous Socket.IO server with permissive CORS for development
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# In-memory mapping of socket sid -> { user_id, username, display_name, role }
connected_clients = {}

@sio.event
async def connect(sid, environ, auth=None):
    """
    Handle client connection with optional JWT auth in handshake.
    """
    user_id = None
    role = "guest"
    display_name = "Anonymous Guest"

    if auth and isinstance(auth, dict):
        user_id = auth.get("user_id")
        role = auth.get("role", "creator")
        display_name = auth.get("display_name", "Creator")

    connected_clients[sid] = {
        "user_id": user_id,
        "role": role,
        "display_name": display_name,
        "connected_at": datetime.now(timezone.utc).isoformat()
    }
    logger.info(f"Socket connected: {sid} (user: {user_id})")
    await sio.emit("connection_ack", {"status": "connected", "sid": sid}, to=sid)


@sio.event
async def disconnect(sid):
    """
    Handle client disconnect and cleanup.
    """
    if sid in connected_clients:
        user_info = connected_clients.pop(sid)
        logger.info(f"Socket disconnected: {sid} (user: {user_info.get('user_id')})")


@sio.event
async def join_project(sid, data):
    """
    Join a project chat room for real-time collaboration.
    data: { "project_id": str, "user_id": str, "display_name": str }
    """
    project_id = data.get("project_id", "default_room")
    room_name = f"project_{project_id}"
    
    # Update socket user metadata if passed
    if sid in connected_clients:
        if data.get("user_id"):
            connected_clients[sid]["user_id"] = data["user_id"]
        if data.get("display_name"):
            connected_clients[sid]["display_name"] = data["display_name"]

    await sio.enter_room(sid, room_name)
    logger.info(f"Socket {sid} joined room {room_name}")

    await sio.emit(
        "room_joined",
        {
            "project_id": project_id,
            "room": room_name,
            "system_message": "Secure anonymous channel active. PII interception enabled."
        },
        to=sid
    )


@sio.event
async def send_message(sid, data):
    """
    Intercept and broadcast chat message.
    Inspects content for PII BEFORE allowing transmission to room members.
    data: {
        "project_id": str,
        "sender_id": str,
        "sender_name": str,
        "content": str
    }
    """
    project_id = data.get("project_id", "default_room")
    sender_id = data.get("sender_id") or connected_clients.get(sid, {}).get("user_id") or "anon_sender"
    sender_name = data.get("sender_name") or connected_clients.get(sid, {}).get("display_name") or "Anonymous Creator"
    raw_content = data.get("content", "").strip()

    if not raw_content:
        return

    room_name = f"project_{project_id}"

    # 1. SCAN FOR PII VIOLATIONS
    scan_result = PIIInterceptorMiddleware.scan_and_redact(raw_content)

    db: Session = SessionLocal()
    try:
        # Find or create linked conversation for this project
        conv = db.query(models.Conversation).filter(models.Conversation.project_id == project_id).first()
        if not conv:
            conv = models.Conversation(
                project_id=project_id,
                created_by=sender_id,
                conversation_type="project"
            )
            db.add(conv)
            db.flush()

        # Check if user has an alias
        sender_profile = db.query(models.Profile).filter(models.Profile.id == sender_id).first()
        effective_sender_name = sender_name
        if sender_profile:
            effective_sender_name = AliasGeneratorService.get_public_name(sender_profile)

        if scan_result["has_pii"]:
            # --- VIOLATION DETECTED: INTERCEPT & BLOCK ---
            logger.warning(f"PII INTERCEPTED from {sender_id}: {scan_result['violations']}")

            # Log violation event to DB with valid conversation foreign key
            PIIInterceptorMiddleware.log_violation_to_db(
                db=db,
                user_id=sender_id,
                channel_type=conv.id,
                scan_result=scan_result
            )

            violation_count = sender_profile.pii_violation_count if sender_profile else 1
            account_suspended = sender_profile.account_status == "suspended" if sender_profile else False

            # Emit PII Blocked alert ONLY to the offending sender socket
            await sio.emit(
                "pii_blocked",
                {
                    "event": "pii_blocked",
                    "reason": "Direct contact information or off-platform handle intercepted.",
                    "violations": scan_result["violations"],
                    "redacted_preview": scan_result["redacted_text"],
                    "violation_count": violation_count,
                    "strikes_remaining": max(0, 7 - violation_count),
                    "is_suspended": account_suspended,
                    "policy": "Hypear AI enforces zero off-platform solicitation to protect escrow funds & IP.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                to=sid
            )
            return

        # --- MESSAGE IS CLEAN: PERSIST & BROADCAST ---
        new_msg = models.Message(
            conversation_id=conv.id,
            sender_id=sender_id,
            body=raw_content,
            created_at=datetime.now(timezone.utc)
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)

        msg_payload = {
            "id": new_msg.id,
            "project_id": project_id,
            "conversation_id": conv.id,
            "sender_id": sender_id,
            "sender_name": effective_sender_name,
            "content": raw_content,
            "created_at": new_msg.created_at.isoformat() if hasattr(new_msg, 'created_at') and new_msg.created_at else datetime.now(timezone.utc).isoformat(),
            "status": "delivered",
            "is_redacted": False
        }

        # Broadcast to everyone in the room
        await sio.emit("message_received", msg_payload, room=room_name)

    except Exception as e:
        logger.error(f"Error handling socket message: {e}", exc_info=True)
        db.rollback()
        await sio.emit("error", {"message": "Failed to process message safely."}, to=sid)
    finally:
        db.close()


@sio.event
async def typing_start(sid, data):
    """Broadcast typing state to room."""
    project_id = data.get("project_id", "default_room")
    user_name = data.get("user_name", "Someone")
    room_name = f"project_{project_id}"
    await sio.emit("user_typing", {"user_name": user_name, "is_typing": True}, room=room_name, skip_sid=sid)


@sio.event
async def typing_stop(sid, data):
    """Broadcast stop typing state to room."""
    project_id = data.get("project_id", "default_room")
    user_name = data.get("user_name", "Someone")
    room_name = f"project_{project_id}"
    await sio.emit("user_typing", {"user_name": user_name, "is_typing": False}, room=room_name, skip_sid=sid)


# Create the ASGI application wrapper
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    socketio_path="socket.io"
)
