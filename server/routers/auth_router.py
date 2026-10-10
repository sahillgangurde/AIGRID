"""
Authentication and Profile Router for FRAME.
Endpoints:
- POST /api/auth/signup
- POST /api/auth/login
- GET  /api/auth/me
- PUT  /api/auth/profile
"""

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import Profile, CreatorProfile, BrandProfile, AuditLog
from server.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class SignupRequest(BaseModel):
    username: str
    password: str
    display_name: str
    role: str = "creator" # creator or brand
    bio: Optional[str] = ""
    avatar_url: Optional[str] = None
    brand_name: Optional[str] = None
    public_alias: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class GoogleSyncRequest(BaseModel):
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    google_id: Optional[str] = None
    role: Optional[str] = "creator"

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # Validate username
    normalized = AuthService.validate_username(req.username)

    # Check case-insensitive uniqueness in database
    existing = db.query(Profile).filter(Profile.normalized_username == normalized).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{req.username}' is already taken."
        )

    if req.role not in ("creator", "brand"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be 'creator' or 'brand'.")

    # Hash password
    pw_hash = AuthService.hash_password(req.password)

    profile = Profile(
        username=req.username,
        normalized_username=normalized,
        password_hash=pw_hash,
        display_name=req.display_name,
        avatar_url=req.avatar_url or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
        bio=req.bio,
        role=req.role,
        account_status="active"
    )
    db.add(profile)
    db.flush()

    if req.role == "creator":
        cp = CreatorProfile(
            user_id=profile.id,
            specializations=json.dumps(["AI Filmmaking", "Generative Direction"]),
            skills=json.dumps(["Prompt Engineering", "Temporal Consistency"]),
            ai_tools=json.dumps(["Runway Gen-3", "ComfyUI"]),
            ai_models=json.dumps(["Flux.1 Dev"]),
            supported_content_types=json.dumps(["Social Video Commercial", "AI Short Film"]),
            aspect_ratios=json.dumps(["9:16 (Vertical Reels/TikTok)", "16:9 (Cinema)"]),
            minimum_budget=2000.0,
            hourly_compute_rate=45.0,
            availability_status="available"
        )
        db.add(cp)
    else:
        bp = BrandProfile(
            user_id=profile.id,
            brand_name=req.brand_name or req.display_name,
            public_alias=req.public_alias or req.display_name,
            is_confidential=False,
            visibility_mode="public",
            industry="Digital Brand",
            organization_details=json.dumps({})
        )
        db.add(bp)

    db.flush()

    # Free-trial subscription: creators get a 90-day free listing trial,
    # brands get an active brand plan (no trial).
    from server.services.subscription_service import SubscriptionService
    SubscriptionService.ensure_subscription(db, profile)

    db.commit()
    db.refresh(profile)

    # Create token
    token = AuthService.create_access_token({"sub": profile.id, "role": profile.role, "username": profile.username})

    # Audit log
    db.add(AuditLog(
        actor_id=profile.id,
        action="USER_SIGNUP",
        resource_type="profile",
        resource_id=profile.id,
        metadata_json=json.dumps({"role": profile.role, "username": profile.username})
    ))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": profile.id,
            "username": profile.username,
            "display_name": profile.display_name,
            "role": profile.role,
            "avatar_url": profile.avatar_url,
            "account_status": profile.account_status
        }
    }

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    normalized = AuthService.normalize_username(req.username)
    user = db.query(Profile).filter(Profile.normalized_username == normalized).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    if not AuthService.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")

    if user.account_status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended.")

    token = AuthService.create_access_token({"sub": user.id, "role": user.role, "username": user.username})

    # Audit log
    db.add(AuditLog(
        actor_id=user.id,
        action="USER_LOGIN",
        resource_type="profile",
        resource_id=user.id,
        metadata_json=json.dumps({"ip": "local_session"})
    ))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "account_status": user.account_status
        }
    }

@router.post("/google-sync")
def google_sync(req: GoogleSyncRequest, db: Session = Depends(get_db)):
    """
    Synchronizes a Supabase / Google OAuth user with the persistent backend database.
    Creates or retrieves the Profile and issues a full backend JWT access token.
    """
    clean_email = req.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid email address is required.")

    normalized = AuthService.normalize_username(clean_email)
    user = db.query(Profile).filter(Profile.normalized_username == normalized).first()

    if not user:
        display_name = req.display_name or (clean_email.split("@")[0].replace(".", " ").title())
        user = Profile(
            username=clean_email[:50],
            normalized_username=normalized[:50],
            password_hash="google_oauth_authenticated",
            display_name=display_name,
            avatar_url=req.avatar_url or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=200&q=80",
            bio=f"AI Creator verified via Google OAuth ({clean_email})",
            role=req.role if req.role in ("creator", "brand") else "creator",
            account_status="active"
        )
        db.add(user)
        db.flush()

        if user.role == "creator":
            cp = CreatorProfile(
                user_id=user.id,
                specializations=json.dumps(["AI Filmmaking", "Generative Direction"]),
                skills=json.dumps(["Prompt Engineering", "Temporal Consistency"]),
                ai_tools=json.dumps(["Midjourney", "Runway Gen-3", "ComfyUI"]),
                ai_models=json.dumps(["Flux.1 Dev"]),
                supported_content_types=json.dumps(["Social Video Commercial", "AI Short Film"]),
                aspect_ratios=json.dumps(["9:16 (Vertical Reels/TikTok)", "16:9 (Cinema)"]),
                minimum_budget=2000.0,
                hourly_compute_rate=45.0,
                availability_status="available"
            )
            db.add(cp)
        else:
            bp = BrandProfile(
                user_id=user.id,
                brand_name=display_name,
                public_alias=display_name,
                is_confidential=False,
                visibility_mode="public",
                industry="Digital Media",
                organization_details=json.dumps({})
            )
            db.add(bp)

        from server.services.subscription_service import SubscriptionService
        SubscriptionService.ensure_subscription(db, user)

        db.commit()
        db.refresh(user)

    if user.account_status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been suspended.")

    # Refresh avatar or display name if provided by Google
    updated = False
    if req.avatar_url and (not user.avatar_url or "unsplash" in user.avatar_url):
        user.avatar_url = req.avatar_url
        updated = True
    if req.display_name and not user.display_name:
        user.display_name = req.display_name
        updated = True
    if updated:
        db.commit()
        db.refresh(user)

    token = AuthService.create_access_token({"sub": user.id, "role": user.role, "username": user.username})

    db.add(AuditLog(
        actor_id=user.id,
        action="GOOGLE_OAUTH_LOGIN",
        resource_type="profile",
        resource_id=user.id,
        metadata_json=json.dumps({"provider": "google", "email": clean_email})
    ))
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "account_status": user.account_status
        }
    }

@router.get("/me")
def get_current_user_profile(user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    result = {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "role": user.role,
        "account_status": user.account_status,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    if user.role == "creator" and user.creator_details:
        cd = user.creator_details
        result["creator_details"] = {
            "specializations": json.loads(cd.specializations or "[]"),
            "skills": json.loads(cd.skills or "[]"),
            "ai_tools": json.loads(cd.ai_tools or "[]"),
            "ai_models": json.loads(cd.ai_models or "[]"),
            "experience_years": cd.experience_years,
            "minimum_budget": cd.minimum_budget,
            "maximum_budget": cd.maximum_budget,
            "hourly_compute_rate": cd.hourly_compute_rate,
            "availability_status": cd.availability_status,
            "accepting_projects": cd.accepting_projects,
            "profile_visibility": cd.profile_visibility
        }
    elif user.role == "brand" and user.brand_details:
        bd = user.brand_details
        result["brand_details"] = {
            "brand_name": bd.brand_name,
            "public_alias": bd.public_alias,
            "visibility_mode": bd.visibility_mode,
            "industry": bd.industry
        }
    return result

@router.put("/profile")
def update_profile(req: ProfileUpdateRequest, user: Profile = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.display_name:
        user.display_name = req.display_name
    if req.bio is not None:
        user.bio = req.bio
    if req.avatar_url:
        user.avatar_url = req.avatar_url
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return {"status": "success", "user": {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio
    }}
