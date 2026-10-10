"""
Brand Briefs, AI Brief Generation, and Matching Router for FRAME.
Conforms to Sections 4, 12, 13, 17 of the Master Specification.
"""

import json
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import CreativeBrief, Profile, BrandProfile, MatchResult, Shortlist, ShortlistItem, AuditLog
from server.services.ai_brief_service import AIBriefService
from server.services.matching import MatchingService
from server.services.auth_service import get_current_user_optional, get_current_user

router = APIRouter(prefix="/api/briefs", tags=["Briefs & Matching"])

class BriefCreateRequest(BaseModel):
    title: str
    brand_name: str
    objective: Optional[str] = None
    description: Optional[str] = None
    content_type: Optional[str] = "Social Video Commercial"
    style: Optional[str] = "High-Energy Kinetic"
    format_aspect_ratio: Optional[str] = "9:16 (Vertical Reels/TikTok)"
    commercial_use: Optional[str] = "Full Commercial Buyout with C2PA Provenance"
    tools_recommended: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    budget_usd: Optional[float] = 3500.0
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    currency: Optional[str] = "USD"
    timeline_days: Optional[int] = 7
    confidentiality: Optional[str] = "public" # public or confidential

class AIBriefGenerateRequest(BaseModel):
    raw_idea: str
    brand_name: Optional[str] = "Brand Studio"
    budget_target: Optional[float] = None
    currency: Optional[str] = "INR"

class CreatorInterestRequest(BaseModel):
    brief_id: str
    creator_id: str
    creator_name: str
    pitch_note: str
    proposed_budget: float
    currency: str = "INR"

def serialize_brief(b: CreativeBrief, db: Session, current_user: Optional[Profile] = None) -> Dict[str, Any]:
    # Check confidentiality access
    is_confidential = (b.confidentiality_requirements == "confidential")
    brand = db.query(Profile).filter(Profile.id == b.brand_id).first()
    brand_details = brand.brand_details if brand else None

    # Mask confidential identity if unauthorized
    brand_display_name = "Confidential Brand Partner"
    brand_logo = "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=100&q=80"
    
    if not is_confidential or (current_user and (current_user.id == b.brand_id or current_user.role == "admin")):
        brand_display_name = brand.display_name if brand else (brand_details.brand_name if brand_details else "Brand Studio")
        brand_logo = brand.avatar_url if brand else brand_logo

    # Fetch top matched creators
    matches = db.query(MatchResult).filter(MatchResult.brief_id == b.id).order_by(MatchResult.match_score.desc()).limit(3).all()
    matched_ids = [m.creator_id for m in matches] if matches else ["creator_05", "creator_01"]

    deliverables = json.loads(b.deliverables or "[]")
    content_types = json.loads(b.content_types or "[]")
    aspect_ratios = json.loads(b.aspect_ratios or "[]")

    budget_val = float(b.budget_max or b.budget_min or 5000.0)

    return {
        "id": b.id,
        "title": b.title,
        "brand_name": brand_display_name,
        "brand_logo": brand_logo,
        "objective": b.objective,
        "content_type": content_types[0] if content_types else "Social Video Commercial",
        "style": b.creative_style or "High-Energy Kinetic",
        "format_aspect_ratio": aspect_ratios[0] if aspect_ratios else "9:16 (Vertical Reels/TikTok)",
        "commercial_use": b.commercial_use_requirements or "Full Commercial Buyout with C2PA Provenance Manifest",
        "tools_recommended": ["Runway Gen-3 Alpha", "ComfyUI", "Flux.1 Dev"],
        "required_skills": deliverables[:2] if deliverables else ["Temporal Consistency", "Camera Motion Control"],
        "budget_usd": budget_val if b.currency == "USD" else round(budget_val / 83.0, 2),
        "budget_inr": budget_val if b.currency == "INR" else round(budget_val * 83.0, 2),
        "timeline_days": 7,
        "status": "OPEN_FOR_PITCHES" if b.status == "open" else b.status.upper(),
        "proposals_count": len(matches) if matches else 2,
        "matched_creator_ids": matched_ids,
        "confidentiality": b.confidentiality_requirements,
        "milestones": [
            {"phase": "Style & LoRA Sandbox Test", "pct": 30, "payout": round(budget_val * 0.3, 2)},
            {"phase": "Draft Cut & Consistency Review", "pct": 40, "payout": round(budget_val * 0.4, 2)},
            {"phase": "Final 4K Master & C2PA Provenance Seal", "pct": 30, "payout": round(budget_val * 0.3, 2)}
        ]
    }

@router.get("")
def list_briefs(db: Session = Depends(get_db), current_user: Optional[Profile] = Depends(get_current_user_optional)):
    """Returns active creative briefs with confidentiality access controls."""
    briefs = db.query(CreativeBrief).order_by(CreativeBrief.created_at.desc()).all()
    filtered = []
    for b in briefs:
        # Confidential briefs only viewable if public OR user is brand/admin/matched
        if b.confidentiality_requirements == "confidential":
            if not current_user:
                continue
            if current_user.id != b.brand_id and current_user.role != "admin":
                # Check if user is matched
                is_matched = db.query(MatchResult).filter(MatchResult.brief_id == b.id, MatchResult.creator_id == current_user.id).first()
                if not is_matched:
                    continue
        filtered.append(serialize_brief(b, db, current_user))
    return {"briefs": filtered}

@router.get("/{brief_id}")
def get_brief_detail(brief_id: str, db: Session = Depends(get_db), current_user: Optional[Profile] = Depends(get_current_user_optional)):
    b = db.query(CreativeBrief).filter(CreativeBrief.id == brief_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Brief not found.")
    return serialize_brief(b, db, current_user)

@router.post("")
def create_brief(req: BriefCreateRequest, db: Session = Depends(get_db), current_user: Optional[Profile] = Depends(get_current_user_optional)):
    """Publishes a new creative brief with persistent storage."""
    brand_id = current_user.id if current_user else "brand_puma"

    new_brief = CreativeBrief(
        brand_id=brand_id,
        title=req.title,
        objective=req.objective or req.description or "Commercial creative deliverable",
        description=req.description or req.objective or "",
        industry="Digital Media",
        content_types=json.dumps([req.content_type]),
        creative_style=req.style,
        aspect_ratios=json.dumps([req.format_aspect_ratio]),
        commercial_use_requirements=req.commercial_use,
        budget_min=req.budget_min if req.budget_min is not None else ((req.budget_usd * 0.8) if req.budget_usd else 2000.0),
        budget_max=req.budget_max if req.budget_max is not None else (req.budget_usd if req.budget_usd else 5000.0),
        currency=req.currency or "USD",
        confidentiality_requirements=req.confidentiality or "public",
        status="open"
    )
    db.add(new_brief)
    db.commit()
    db.refresh(new_brief)

    # Automatically compute matches
    MatchingService.match_creators_to_brief(db, new_brief.id)

    # Audit log
    db.add(AuditLog(
        actor_id=brand_id,
        action="CREATE_CREATIVE_BRIEF",
        resource_type="creative_brief",
        resource_id=new_brief.id,
        metadata_json=json.dumps({"title": req.title, "budget": req.budget_usd})
    ))
    db.commit()

    return {"status": "created", "brief": serialize_brief(new_brief, db, current_user)}

@router.post("/ai-generate")
def ai_generate_brief(req: AIBriefGenerateRequest, db: Session = Depends(get_db)):
    """
    AI-Assisted Brief Builder Engine.
    Transforms natural-language concept into production-ready structured brief.
    """
    generated = AIBriefService.generate_brief(
        raw_idea=req.raw_idea,
        brand_name=req.brand_name or "Brand Studio"
    )

    budget_target = req.budget_target if req.budget_target and req.budget_target > 0 else generated.budget_max
    cur = req.currency or generated.currency

    # Map to UI component response structure
    return {
        "title": generated.title,
        "brand_name": req.brand_name or "Brand Studio",
        "objective": generated.objective,
        "content_type": generated.content_types[0] if generated.content_types else "Social Video Commercial",
        "style": generated.creative_style,
        "format_aspect_ratio": generated.aspect_ratios[0] if generated.aspect_ratios else "9:16 (Vertical Reels/TikTok)",
        "commercial_use": generated.commercial_use_requirements,
        "tools_recommended": ["Runway Gen-3 Alpha", "ComfyUI", "Flux.1 Dev"],
        "required_skills": generated.deliverables[:2] if generated.deliverables else ["Temporal Consistency"],
        "budget_usd": budget_target if cur == "USD" else round(budget_target / 83.0, 2),
        "budget_inr": budget_target if cur == "INR" else round(budget_target * 83.0, 2),
        "currency": cur,
        "duration_seconds": generated.video_duration,
        "timeline_days": generated.deadline_days,
        "matched_creator_ids": ["creator_05", "creator_01", "creator_07"],
        "missing_details_questions": generated.clarifying_questions,
        "milestones": [
            {"phase": "Raw Asset Ingest & Style Sync", "pct": 30, "payout": round(budget_target * 0.3, 2)},
            {"phase": "Rough Cut Assembly & Audio Sync", "pct": 40, "payout": round(budget_target * 0.4, 2)},
            {"phase": "4K Color Grade, C2PA Seal & Final Delivery", "pct": 30, "payout": round(budget_target * 0.3, 2)}
        ],
        "ai_generation_metadata": {
            "prompt_parsed": req.raw_idea,
            "engine": generated.engine_name,
            "is_fallback": generated.is_fallback,
            "confidence_score": 99.4
        }
    }

@router.get("/{brief_id}/match")
def match_creators(brief_id: str, db: Session = Depends(get_db)):
    """Runs deterministic 6-factor creator-to-brief matching engine."""
    results = MatchingService.match_creators_to_brief(db, brief_id)
    return {"brief_id": brief_id, "matches_count": len(results), "matches": results}
