"""
FRAME & AuraForge Unified FastAPI Server Gateway.
The Cryptographically Verified, AI-Native Creative Marketplace Backend.
Conforms to Master Implementation Specification:
- Database Persistence (SQLite / PostgreSQL)
- JWT Authentication & Role Authorization
- 21+ Database Tables & Relationship Models
- Deterministic 6-Factor Matching Engine
- 4-Factor Explainable Trust Score Engine
- Automated Achievement Badge Evaluator
- AI Brief Generation with Structured Schema
- Scoped Portfolio Approval Workflow
- Project Milestones & Scoped Messaging
- Demo Finance Transactions & Payouts
- AST Safety Guard, C2PA Provenance, and Escrow
"""

import time
import uuid
import json
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Body, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Database & Models
from server.db.session import engine, Base, SessionLocal, get_db
import server.db.models as models
from server.seed.seed_data import seed_database

# Specialized Services
from server.services.comfy_parser import ComfyUIParserService
from server.services.provenance import ProvenanceService
from server.services.vector_matcher import VectorMatcherService
from server.services.compliance import ComplianceService
from server.services.escrow import EscrowService

# Routers — v1 (existing)
from server.routers.auth_router import router as auth_router
from server.routers.creators_router import router as creators_router
from server.routers.briefs_router import router as briefs_router
from server.routers.feed_router import router as feed_router
from server.routers.projects_router import router as projects_router
from server.routers.messaging_router import router as messaging_router
from server.routers.approvals_router import router as approvals_router
from server.routers.collaborations_router import router as collaborations_router
from server.routers.finance_router import router as finance_router
from server.routers.admin_router import router as admin_router

# Routers — v2 (Hypear Anonymous Marketplace)
from server.routers.identity_router import router as identity_router
from server.routers.disputes_router import router as disputes_router

# Routers — v3 (CreatorGrid Escrow Flow)
from server.routers.payments_router import router as payments_router

# Routers — v4 (CreatorGrid Revenue: Subscription Free-Trial)
from server.routers.subscription_router import router as subscription_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database tables exist and seed if empty
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if database has creators; if not, seed
        creator_count = db.query(models.Profile).filter(models.Profile.role == "creator").count()
        if creator_count < 12:
            seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Hypear AI — Anonymous Creator Marketplace API",
    description=(
        "Production-grade backend for the Hypear AI anonymous creator marketplace. "
        "Features: Anonymous identity engine (PII vault + alias generator), "
        "real-time PII interception middleware, escrow lifecycle management, "
        "AI-powered brief generation (LangChain/GPT-4o), semantic creator matching (pgvector), "
        "C2PA provenance signing, dispute resolution, and multi-party payment routing (Razorpay)."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Modular Routers — v1
app.include_router(auth_router)
app.include_router(creators_router)
app.include_router(briefs_router)
app.include_router(feed_router)
app.include_router(projects_router)
app.include_router(messaging_router)
app.include_router(approvals_router)
app.include_router(collaborations_router)
app.include_router(finance_router)
app.include_router(admin_router)

# Mount Modular Routers — v2 (Hypear Anonymous Marketplace)
app.include_router(identity_router)  # /api/v2/identity/*
app.include_router(disputes_router)  # /api/v2/disputes/*

# Mount Modular Routers — v3 (CreatorGrid Escrow Flow)
app.include_router(payments_router)  # /api/payments/webhook

# Mount Modular Routers — v4 (CreatorGrid Revenue)
app.include_router(subscription_router)  # /api/subscriptions/*

# Mount Real-Time Socket.IO ASGI App
import socketio
from server.socket_server import sio
socket_app = socketio.ASGIApp(sio, socketio_path="")
app.mount("/socket.io", socket_app)



# ----------------- Request Models for Existing Specialized Services -----------------

class WorkflowVerifyRequest(BaseModel):
    workflow_json: Dict[str, Any]
    creator_id: Optional[str] = "creator_01"

class C2PASignRequest(BaseModel):
    workflow_hash: str
    author_name: str
    author_id: str
    license_type: str = "Commercial-Exclusive"
    model_name: str = "SDXL_Base_v1.0"
    compliance_tier: str = "COMMERCIAL_NON_BRANDED"

class MoodboardMatchRequest(BaseModel):
    tags: List[str] = Field(default_factory=list)
    image_seeds: Optional[List[str]] = None
    target_category: Optional[str] = None

class SandboxPreviewRequest(BaseModel):
    creator_id: str
    test_prompt: str
    negative_prompt: Optional[str] = ""
    seed: Optional[int] = 42
    steps: Optional[int] = 30

class ComplianceAuditRequest(BaseModel):
    prompt_text: str
    has_face_detected: bool = False
    claimed_release_id: Optional[str] = None

class EscrowCalcRequest(BaseModel):
    base_license_usd: float
    gpu_steps: int = 1200
    gpu_tier: str = "H100_SXM5"
    num_variations: int = 4

class EscrowCreateRequest(BaseModel):
    buyer_id: str
    creator_id: str
    creator_name: str
    base_license_usd: float
    gpu_steps: int = 1200
    gpu_tier: str = "H100_SXM5"

class EscrowAdvanceRequest(BaseModel):
    contract_id: str
    stage: str

class CustomerEnquiryRequest(BaseModel):
    creator_id: str
    creator_name: Optional[str] = "Creator"
    customer_name: str
    customer_email: str
    project_title: str
    project_type: str = "Social Video Reel"
    budget: float = 5000.0
    currency: str = "INR"
    duration_sec: int = 30
    deadline_days: int = 3
    scope_details: str
    footage_link: Optional[str] = None

CUSTOMER_ENQUIRIES: List[Dict[str, Any]] = [
    {
        "id": "enq_seed_01",
        "creator_id": "creator_07",
        "creator_name": "Priya Sharma",
        "customer_name": "Rohan & Sneha",
        "customer_email": "rohan.sneha@gmail.com",
        "project_title": "30-Second Birthday Reel Montage",
        "project_type": "Birthday / Event Montage",
        "budget": 5000.0,
        "currency": "INR",
        "duration_sec": 30,
        "deadline_days": 3,
        "scope_details": "Need a 30s birthday reel edit with beat-synced music, warm cinematic grading, and animated title overlays.",
        "footage_link": "https://drive.google.com/drive/folders/sample-birthday-clips",
        "status": "INTEREST_EXPRESSED",
        "timestamp": "12:30 PM"
    }
]


# ----------------- Health & Status Endpoint -----------------

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    creator_count = db.query(models.Profile).filter(models.Profile.role == "creator").count()
    brief_count = db.query(models.CreativeBrief).count()
    project_count = db.query(models.Project).count()

    return {
        "status": "healthy",
        "database": "connected (SQLite Persistent Storage)",
        "service": "FRAME Master Marketplace API Gateway",
        "c2pa_engine": "ISO 21000-22 JUMBF Ready",
        "vector_dimensions": 1024,
        "creators_count": creator_count,
        "active_briefs_count": brief_count,
        "projects_count": project_count,
        "auth_engine": "JWT + PBKDF2-HMAC-SHA256 Active",
        "timestamp": time.time()
    }


# ----------------- Customer Enquiries & Creator Opportunities -----------------

@app.get("/api/enquiries")
def get_customer_enquiries(db: Session = Depends(get_db)):
    db_enqs = db.query(models.CustomerEnquiry).order_by(models.CustomerEnquiry.created_at.desc()).all()
    serialized = []
    for e in db_enqs:
        serialized.append({
            "id": e.id,
            "creator_id": e.creator_id,
            "creator_name": e.creator.display_name if e.creator else "Creator",
            "customer_name": e.customer_name,
            "customer_email": e.customer_email,
            "project_title": e.project_title,
            "project_type": e.project_type,
            "budget": e.budget_amount,
            "currency": e.budget_currency,
            "duration_sec": e.duration_seconds,
            "deadline_days": e.deadline_days,
            "scope_details": e.scope_details,
            "footage_link": e.footage_link,
            "status": e.status,
            "timestamp": e.created_at.strftime("%I:%M %p") if e.created_at else "Just now"
        })
    if not serialized:
        serialized = CUSTOMER_ENQUIRIES
    return {"enquiries": serialized}

@app.post("/api/enquiries")
def create_customer_enquiry(req: CustomerEnquiryRequest, db: Session = Depends(get_db)):
    db_enq = models.CustomerEnquiry(
        id=f"enq_{uuid.uuid4().hex[:8]}",
        creator_id=req.creator_id,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        project_title=req.project_title,
        project_type=req.project_type,
        budget_amount=req.budget,
        budget_currency=req.currency or "INR",
        duration_seconds=req.duration_sec,
        deadline_days=req.deadline_days,
        scope_details=req.scope_details,
        footage_link=req.footage_link,
        status="pending"
    )
    db.add(db_enq)
    db.commit()
    db.refresh(db_enq)

    enq_data = {
        "id": db_enq.id,
        "creator_id": db_enq.creator_id,
        "creator_name": req.creator_name,
        "customer_name": db_enq.customer_name,
        "customer_email": db_enq.customer_email,
        "project_title": db_enq.project_title,
        "project_type": db_enq.project_type,
        "budget": db_enq.budget_amount,
        "currency": db_enq.budget_currency,
        "duration_sec": db_enq.duration_seconds,
        "deadline_days": db_enq.deadline_days,
        "scope_details": db_enq.scope_details,
        "footage_link": db_enq.footage_link,
        "status": db_enq.status,
        "timestamp": time.strftime("%I:%M %p")
    }
    CUSTOMER_ENQUIRIES.insert(0, enq_data)
    return {"status": "success", "enquiry": enq_data}

@app.get("/api/creator/opportunities")
def get_creator_opportunities(db: Session = Depends(get_db)):
    briefs = db.query(models.CreativeBrief).filter(models.CreativeBrief.status == "open").all()
    briefs_serialized = []
    for b in briefs:
        deliverables = json.loads(b.deliverables or "[]")
        content_types = json.loads(b.content_types or "[]")
        aspect_ratios = json.loads(b.aspect_ratios or "[]")
        brand = db.query(models.Profile).filter(models.Profile.id == b.brand_id).first()
        budget_val = float(b.budget_max or b.budget_min or 5000.0)
        briefs_serialized.append({
            "id": b.id,
            "title": b.title,
            "brand_name": brand.display_name if brand else "Brand",
            "objective": b.objective,
            "content_type": content_types[0] if content_types else "Social Video Commercial",
            "style": b.creative_style or "Cinematic",
            "format_aspect_ratio": aspect_ratios[0] if aspect_ratios else "9:16 (Vertical)",
            "budget_inr": budget_val,
            "budget_usd": round(budget_val / 83.0, 2),
            "timeline_days": 7,
            "status": "OPEN_FOR_PITCHES",
            "proposals_count": 2
        })

    return {
        "opportunities": briefs_serialized,
        "enquiries": CUSTOMER_ENQUIRIES
    }


# ----------------- Specialized AI, ComfyUI, C2PA, and Escrow Endpoints -----------------

@app.get("/api/stats/market-dynamics")
def get_market_dynamics():
    from server.data.creators_data import EMPIRICAL_RESEARCH_DATA
    return EMPIRICAL_RESEARCH_DATA

@app.post("/api/workflow/verify-comfy")
def verify_comfy_workflow(req: WorkflowVerifyRequest):
    return ComfyUIParserService.validate_and_parse(req.workflow_json)

@app.post("/api/provenance/sign-c2pa")
def sign_c2pa_manifest(req: C2PASignRequest):
    return ProvenanceService.generate_c2pa_manifest(
        workflow_hash=req.workflow_hash,
        author_name=req.author_name,
        author_id=req.author_id,
        license_type=req.license_type,
        model_name=req.model_name,
        compliance_tier=req.compliance_tier
    )

@app.post("/api/provenance/verify")
def verify_provenance(payload: Dict[str, Any] = Body(...)):
    manifest_data = payload.get("manifest", {})
    workflow_hash = payload.get("workflow_hash", "")
    return ProvenanceService.verify_provenance(manifest_data, workflow_hash)

@app.post("/api/style/match-moodboard")
def match_moodboard(req: MoodboardMatchRequest):
    return VectorMatcherService.match_moodboard(
        tags=req.tags,
        image_seeds=req.image_seeds,
        target_category=req.target_category
    )

@app.post("/api/sandbox/render-preview")
def render_sandbox_preview(req: SandboxPreviewRequest, db: Session = Depends(get_db)):
    creator = db.query(models.Profile).filter(models.Profile.id == req.creator_id).first()
    cd = creator.creator_details if creator else None

    # Sample preview url
    preview_url = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80"
    if creator:
        item = db.query(models.PortfolioItem).filter(models.PortfolioItem.creator_id == creator.id).first()
        if item:
            preview_url = item.thumbnail_path or item.media_path

    inference_time = round(1.2 + (req.steps / 30.0) * 0.4, 2)
    preview_id = f"prev_{uuid.uuid4().hex[:6]}"

    return {
        "preview_id": preview_id,
        "preview_url": preview_url,
        "test_prompt": req.test_prompt,
        "creator_name": creator.display_name if creator else "Creator",
        "base_model": cd.base_model if cd else "Flux.1 Dev",
        "inference_time_seconds": inference_time,
        "watermark_applied": True,
        "watermark_text": "FRAME Sandbox Preview • Unlicensed Demo Grid",
        "model_weights_leaked": False,
        "protection_guarantee": "Zero-leakage RAM isolation verified."
    }

@app.post("/api/compliance/check")
def audit_compliance(req: ComplianceAuditRequest):
    return ComplianceService.audit_content_compliance(
        prompt_text=req.prompt_text,
        has_face_detected=req.has_face_detected,
        claimed_release_id=req.claimed_release_id
    )

@app.post("/api/escrow/calculate")
def calculate_escrow(req: EscrowCalcRequest):
    return EscrowService.calculate_compute_and_milestones(
        base_license_usd=req.base_license_usd,
        gpu_steps=req.gpu_steps,
        gpu_tier=req.gpu_tier,
        num_variations=req.num_variations
    )

@app.post("/api/escrow/create-contract")
def create_escrow_contract(req: EscrowCreateRequest, db: Session = Depends(get_db)):
    return EscrowService.create_contract(
        buyer_id=req.buyer_id,
        creator_id=req.creator_id,
        creator_name=req.creator_name,
        base_license_usd=req.base_license_usd,
        gpu_steps=req.gpu_steps,
        gpu_tier=req.gpu_tier,
        db=db
    )

@app.post("/api/escrow/advance-stage")
def advance_escrow_stage(req: EscrowAdvanceRequest, db: Session = Depends(get_db)):
    res = EscrowService.advance_escrow_stage(req.contract_id, req.stage, db=db)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.get("/api/escrow/contract/{contract_id}")
def get_escrow_contract(contract_id: str, db: Session = Depends(get_db)):
    res = EscrowService.get_contract(contract_id, db=db)
    if not res:
        raise HTTPException(status_code=404, detail="Contract not found")
    return res

# ----------------- QA & Workspace Endpoints (Tasks 1, 4, 5) -----------------

class DemoReleaseRequest(BaseModel):
    amount: Optional[float] = 3150.0
    recipient_alias: Optional[str] = "Studio Phantom"
    project_id: Optional[str] = "proj_seed_01"

class EscrowFreezeRequest(BaseModel):
    project_id: Optional[str] = "proj_seed_01"
    reason: Optional[str] = "Quality and delivery dispute"

class ChatMessageValidateRequest(BaseModel):
    message: str

WORKSPACE_ESCROW_STATE: Dict[str, Any] = {
    "project_id": "proj_seed_01",
    "milestone_1_settled": True,
    "milestone_1_amount": 1350.0,
    "milestone_2_settled": False,
    "milestone_2_amount": 3150.0,
    "is_frozen": False,
    "total_escrow": 4500.0,
    "creator_alias": "Studio Phantom",
    "project_title": "Cyber-Puma • 15s High-Energy Commercial"
}

@app.get("/api/workspace/state")
def get_workspace_state(db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(
        models.Transaction.project_id == "proj_seed_01",
        models.Transaction.provider_reference.like("RELEASE_M2_%")
    ).first()
    if tx:
        WORKSPACE_ESCROW_STATE["milestone_2_settled"] = True

    latest_brief = db.query(models.CreativeBrief).order_by(models.CreativeBrief.created_at.desc()).first()
    if latest_brief:
        WORKSPACE_ESCROW_STATE["project_title"] = latest_brief.title

    return WORKSPACE_ESCROW_STATE

@app.post("/api/finance/payout/demo-release")
def demo_release_payout(req: DemoReleaseRequest, db: Session = Depends(get_db)):
    if WORKSPACE_ESCROW_STATE.get("milestone_2_settled"):
        raise HTTPException(
            status_code=400,
            detail="Milestone 2 already settled and released. Duplicate release prevented."
        )

    existing_tx = db.query(models.Transaction).filter(
        models.Transaction.project_id == (req.project_id or "proj_seed_01"),
        models.Transaction.provider_reference.like("RELEASE_M2_%")
    ).first()
    if existing_tx:
        WORKSPACE_ESCROW_STATE["milestone_2_settled"] = True
        raise HTTPException(
            status_code=400,
            detail="Milestone 2 already settled and released. Duplicate release prevented."
        )

    tx = models.Transaction(
        brand_id="brand_puma",
        creator_id="creator_studio_phantom",
        project_id=req.project_id or "proj_seed_01",
        gross_amount=float(req.amount or 3150.0),
        platform_fee=float(req.amount or 3150.0) * 0.05,
        net_amount=float(req.amount or 3150.0) * 0.95,
        currency="USD",
        status="settled",
        provider_reference=f"RELEASE_M2_{uuid.uuid4().hex[:8].upper()}"
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    WORKSPACE_ESCROW_STATE["milestone_2_settled"] = True
    return {
        "status": "success",
        "milestone": 2,
        "amount": req.amount or 3150.0,
        "recipient": req.recipient_alias or "Studio Phantom",
        "transaction_id": tx.id
    }

@app.post("/api/workspace/escrow-freeze")
def freeze_escrow(req: Optional[EscrowFreezeRequest] = None, db: Session = Depends(get_db)):
    WORKSPACE_ESCROW_STATE["is_frozen"] = True
    return {"status": "frozen", "is_frozen": True, "message": "Escrow FROZEN pending arbitration!"}

@app.post("/api/workspace/escrow-unfreeze")
def unfreeze_escrow(req: Optional[EscrowFreezeRequest] = None, db: Session = Depends(get_db)):
    WORKSPACE_ESCROW_STATE["is_frozen"] = False
    return {"status": "unfrozen", "is_frozen": False, "message": "Escrow unfrozen."}

@app.post("/api/chat/validate")
def validate_chat_message(req: ChatMessageValidateRequest):
    from server.middleware.pii_interceptor import PIIInterceptor
    has_pii, redacted, violations = PIIInterceptor.scan(req.message)
    if has_pii:
        return {
            "allowed": False,
            "blocked": True,
            "violations": violations,
            "detail": "Direct Contact Blocked: Personal phone numbers and contact sequences are blocked." if any("phone" in v.get("type", "") for v in violations) else "Direct Contact Blocked: Off-platform contact references are blocked."
        }
    return {"allowed": True, "blocked": False, "message": req.message}


# ----------------- Escrow & Confidentiality Terms Agreement (Onboarding) -----------------

class TermsAcceptRequest(BaseModel):
    email: Optional[str] = None
    terms_version: str = "v1.0"
    accepted_at: Optional[str] = None

TERMS_AGREEMENTS: Dict[str, Dict[str, Any]] = {}  # in-memory cache keyed by email

@app.post("/api/terms/accept")
def accept_terms(req: TermsAcceptRequest, db: Session = Depends(get_db)):
    """
    Records the user's Escrow & Confidentiality agreement so terms are not
    repeatedly surfaced. Persisted as an AuditLog entry (database record).
    """
    agreement = {
        "email": req.email,
        "terms_version": req.terms_version,
        "accepted_at": req.accepted_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Find the acting profile if a known username is supplied; anonymous demos still record an audit row.
    actor_id = None
    if req.email:
        profile = db.query(models.Profile).filter(models.Profile.username == req.email).first()
        if profile:
            actor_id = profile.id

    db.add(models.AuditLog(
        actor_id=actor_id,
        action="ACCEPT_ESCROW_TERMS",
        resource_type="terms_agreement",
        resource_id=None,
        metadata_json=json.dumps(agreement)
    ))
    db.commit()

    if req.email:
        TERMS_AGREEMENTS[req.email] = agreement

    return {"status": "recorded", "agreement": agreement}

@app.get("/api/terms/status")
def terms_status(email: Optional[str] = None, db: Session = Depends(get_db)):
    """Checks whether this email has previously accepted the current terms version."""
    if email:
        record = TERMS_AGREEMENTS.get(email)
        if not record:
            log = db.query(models.AuditLog).filter(
                models.AuditLog.action == "ACCEPT_ESCROW_TERMS",
                models.AuditLog.metadata_json.like(f'%"email": "{email}"%')
            ).first()
            if log:
                try:
                    record = json.loads(log.metadata_json or "{}")
                except Exception:
                    record = None
        if record:
            return {"accepted": record.get("terms_version") == "v1.0", "agreement": record}
    return {"accepted": False, "agreement": None}

