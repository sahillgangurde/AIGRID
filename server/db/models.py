"""
SQLAlchemy ORM models for FRAME — AI Creator Marketplace.
Implements complete database schemas conforming to Section 4 of the master specification.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Table, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from server.db.session import Base

def gen_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(50), unique=True, nullable=False)
    normalized_username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(String(20), nullable=False, default="creator") # creator, brand, admin

    # Anonymous Identity Fields (Phase 2)
    masked_alias = Column(String(100), nullable=True, index=True)   # e.g. "Studio Phantom"
    anonymous_mode = Column(Boolean, default=False)                  # hides real display_name
    pii_violation_count = Column(Integer, default=0)                 # increments on each intercept
    fcm_token = Column(Text, nullable=True)                          # Firebase push token

    account_status = Column(String(20), nullable=False, default="active") # active, suspended, pending_review
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    creator_details = relationship("CreatorProfile", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    brand_details = relationship("BrandProfile", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    verification_records = relationship("VerificationRecord", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    portfolio_items = relationship("PortfolioItem", back_populates="creator", cascade="all, delete-orphan")
    feed_posts = relationship("FeedPost", back_populates="creator", cascade="all, delete-orphan")
    pii_vault = relationship("PIIVault", back_populates="profile", uselist=False, cascade="all, delete-orphan")


class CreatorProfile(Base):
    __tablename__ = "creator_profiles"

    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    specializations = Column(Text, default="[]") # JSON list
    skills = Column(Text, default="[]") # JSON list
    industries = Column(Text, default="[]") # JSON list
    ai_tools = Column(Text, default="[]") # JSON list
    ai_models = Column(Text, default="[]") # JSON list
    workflow_description = Column(Text, nullable=True)
    experience_years = Column(Float, default=1.0)
    supported_content_types = Column(Text, default="[]") # JSON list
    supported_platforms = Column(Text, default="[]") # JSON list
    aspect_ratios = Column(Text, default="[]") # JSON list
    minimum_budget = Column(Float, default=0.0)
    maximum_budget = Column(Float, nullable=True)
    hourly_compute_rate = Column(Float, default=40.0)
    base_model = Column(String(100), default="Flux.1 Dev + ComfyUI")
    availability_status = Column(String(20), default="available") # available, busy, unavailable
    accepting_projects = Column(Boolean, default=True)
    profile_visibility = Column(String(20), default="public") # public, private, unlisted
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    profile = relationship("Profile", back_populates="creator_details")


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    brand_name = Column(String(150), nullable=False)
    public_alias = Column(String(150), nullable=True)
    visibility_mode = Column(String(20), default="public") # public, confidential
    is_confidential = Column(Boolean, default=False)
    masked_brand_name = Column(String(150), default="Confidential Brand Partner")
    industry = Column(String(100), nullable=True)
    organization_details = Column(Text, default="{}") # JSON confidential details
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    profile = relationship("Profile", back_populates="brand_details")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(100), nullable=False)
    media_path = Column(Text, nullable=False)
    thumbnail_path = Column(Text, nullable=True)
    skills = Column(Text, default="[]") # JSON list
    industries = Column(Text, default="[]") # JSON list
    style_tags = Column(Text, default="[]") # JSON list
    ai_tools = Column(Text, default="[]") # JSON list
    ai_models = Column(Text, default="[]") # JSON list
    workflow = Column(Text, default="{}") # JSON DAG or settings
    aspect_ratio = Column(String(30), default="16:9")
    creator_role = Column(String(100), default="Director & Generative Artist")
    visibility = Column(String(30), default="public") # public, unlisted, private, requires_approval
    evidence_status = Column(String(30), default="unverified") # unverified, ast_verified, c2pa_signed, disputed
    rights_status = Column(String(30), default="creator_owned") # creator_owned, client_licensed, public_domain, restricted
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    creator = relationship("Profile", back_populates="portfolio_items")


class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_item_id = Column(String(36), ForeignKey("portfolio_items.id", ondelete="SET NULL"), nullable=True)
    caption = Column(Text, nullable=True)
    media_path = Column(Text, nullable=False)
    thumbnail_path = Column(Text, nullable=True)
    content_type = Column(String(100), nullable=False)
    style_tags = Column(Text, default="[]") # JSON list
    ai_tools = Column(Text, default="[]") # JSON list
    ai_models = Column(Text, default="[]") # JSON list
    visibility = Column(String(20), default="public") # public, private, restricted
    moderation_status = Column(String(20), default="approved") # pending, approved, flagged, removed
    published_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    creator = relationship("Profile", back_populates="feed_posts")


class Like(Base):
    __tablename__ = "likes"

    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(String(36), ForeignKey("feed_posts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Save(Base):
    __tablename__ = "saves"

    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(String(36), ForeignKey("feed_posts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    followed_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        CheckConstraint("follower_id != followed_id", name="disallow_self_follow_check"),
    )


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_type = Column(String(50), nullable=False) # identity_kyc, tool_certification, company_registration
    provider_reference = Column(String(100), nullable=True)
    status = Column(String(30), default="not_started") # not_started, pending, verified, failed, needs_review
    is_demo = Column(Boolean, default=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("Profile", back_populates="verification_records")


class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    eligibility_rules = Column(Text, default="{}") # JSON rules
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = Column(String(36), ForeignKey("achievement_definitions.id", ondelete="CASCADE"), nullable=False)
    earned_at = Column(DateTime(timezone=True), default=utc_now)
    evidence_reference = Column(Text, nullable=True)
    status = Column(String(20), default="active") # active, revoked, under_review

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )

    user = relationship("Profile", back_populates="achievements")
    definition = relationship("AchievementDefinition")


class TrustEvent(Base):
    __tablename__ = "trust_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), nullable=True)
    event_type = Column(String(50), nullable=False) # project_completed_on_time, project_completed_late, repeat_client_hired, documented_milestone_sealed, client_dispute_filed
    event_status = Column(String(20), default="verified") # pending, verified, disputed, rejected
    evidence_reference = Column(Text, nullable=True)
    reviewed_by = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class CreativeBrief(Base):
    __tablename__ = "creative_briefs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    brand_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    objective = Column(Text, nullable=False)
    industry = Column(String(100), nullable=True)
    target_audience = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    deliverables = Column(Text, default="[]") # JSON list
    content_types = Column(Text, default="[]") # JSON list
    creative_style = Column(String(150), nullable=True)
    platforms = Column(Text, default="[]") # JSON list
    aspect_ratios = Column(Text, default="[]") # JSON list
    resolution_requirements = Column(String(50), default="4K UHD")
    video_duration = Column(Integer, default=30)
    quantity = Column(Integer, default=1)
    budget_min = Column(Float, default=0.0)
    budget_max = Column(Float, default=0.0)
    currency = Column(String(10), default="INR")
    deadline = Column(DateTime(timezone=True), nullable=True)
    revision_requirements = Column(Text, nullable=True)
    commercial_use_requirements = Column(Text, nullable=True)
    usage_territory = Column(String(100), default="Worldwide")
    license_duration = Column(String(50), default="1 Year")
    exclusivity_requirements = Column(Text, nullable=True)
    confidentiality_requirements = Column(String(20), default="public") # public, confidential
    is_confidential = Column(Boolean, default=False)
    masked_brand_name = Column(String(150), default="Confidential Brand Partner")
    acceptance_criteria = Column(Text, nullable=True)
    status = Column(String(30), default="open") # draft, open, in_review, awarded, completed, closed
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    brand = relationship("Profile", foreign_keys=[brand_id])


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    brief_id = Column(String(36), ForeignKey("creative_briefs.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, nullable=False)
    component_scores = Column(Text, default="{}") # JSON dict
    match_reasons = Column(Text, default="[]") # JSON list
    compatibility_gaps = Column(Text, default="[]") # JSON list
    rights_status = Column(String(50), default="clear")
    calculated_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("brief_id", "creator_id", name="uq_brief_creator_match"),
    )


class Shortlist(Base):
    __tablename__ = "shortlists"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    owner_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    brief_id = Column(String(36), ForeignKey("creative_briefs.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class ShortlistItem(Base):
    __tablename__ = "shortlist_items"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    shortlist_id = Column(String(36), ForeignKey("shortlists.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("shortlist_id", "creator_id", name="uq_shortlist_creator"),
    )


class Collaboration(Base):
    __tablename__ = "collaborations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), nullable=True)
    initiator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    invitee_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="pending") # pending, accepted, rejected, withdrawn, completed
    roles = Column(Text, default="[]") # JSON list
    attribution_details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        CheckConstraint("initiator_id != invitee_id", name="disallow_self_collab_check"),
    )


class PortfolioApprovalRequest(Base):
    __tablename__ = "portfolio_approval_requests"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), nullable=True, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_item_id = Column(String(36), ForeignKey("portfolio_items.id", ondelete="SET NULL"), nullable=True)
    requested_media_scope = Column(Text, nullable=False) # e.g. "15s excerpt only, not full master"
    requested_metadata_scope = Column(Text, nullable=False)
    requested_platforms = Column(Text, default="[]") # JSON list
    embargo_until = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), default="pending_approval") # draft, pending_approval, changes_requested, approved, rejected, expired, revoked
    decision_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    brand_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    brief_id = Column(String(36), ForeignKey("creative_briefs.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)
    status = Column(String(30), default="in_discussion") # draft, contacted, in_discussion, in_production, submitted_for_review, revision_requested, delivered, cancelled, disputed
    visibility_mode = Column(String(20), default="public") # public, confidential
    identity_revealed = Column(Boolean, default=False)
    budget_amount = Column(Float, default=0.0)
    currency = Column(String(10), default="INR")

    # ── Advance Deposit & Markup Pricing (CreatorGrid Escrow Flow) ──
    # Creator quotes their take-home (e.g. ₹1,00,000). Brand sees quote × (1 + markup_percent)
    # (e.g. ₹1,20,000). The advance deposit (markup portion) is locked in escrow BEFORE
    # contact reveal is allowed — this is the platform's anti-disintermediation moat.
    creator_quote_amount = Column(Float, nullable=True)          # what creator asked (their net)
    markup_percent = Column(Float, default=0.20)                 # platform margin added for brand (0.20 = 20%)
    brand_payable_amount = Column(Float, nullable=True)          # creator_quote * (1 + markup_percent)
    advance_amount = Column(Float, nullable=True)                # upfront deposit locked in escrow
    escrow_state = Column(String(30), default="pending_advance") # pending_advance | advance_locked | settled | refunded
    advance_locked_at = Column(DateTime(timezone=True), nullable=True)
    contact_unlocked_at = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), default=utc_now)
    deadline = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    brand = relationship("Profile", foreign_keys=[brand_id])
    creator = relationship("Profile", foreign_keys=[creator_id])
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    amount = Column(Float, default=0.0)
    percentage = Column(Integer, default=0)
    status = Column(String(30), default="pending") # pending, in_progress, submitted, approved, rejected
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="milestones")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    created_by = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_type = Column(String(30), default="direct") # direct, project, collaboration
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), default=utc_now)
    last_read_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("Profile")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    body = Column(Text, nullable=False)
    attachment_reference = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("Profile")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    brand_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    gross_amount = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False) # e.g. 10%
    net_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="demo_completed") # pending, held_in_escrow, released, refunded, disputed, demo_completed
    provider_reference = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class PayoutRecord(Base):
    __tablename__ = "payout_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(30), default="demo_settled") # pending, processing, completed, failed, demo_settled
    provider_reference = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_code = Column(String(50), nullable=False) # free_creator, pro_creator, studio_brand, enterprise_brand
    status = Column(String(30), default="demo_active") # active, past_due, cancelled, demo_active
    billing_provider = Column(String(50), default="demo_provider")
    provider_subscription_reference = Column(String(100), nullable=True)
    current_period_start = Column(DateTime(timezone=True), default=utc_now)
    current_period_end = Column(DateTime(timezone=True), default=utc_now)

    # ── Creator Free-Trial Enforcement (CreatorGrid revenue model) ──
    # Creators get a 90-day free listing trial. After expiry they must upgrade to
    # pro_creator (paid) or their directory/feed listing is paused (is_listed=False).
    trial_start = Column(DateTime(timezone=True), default=utc_now)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    is_listed = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AdvanceRequest(Base):
    """
    Creator-custom advance request — the flexible advance flow.
    Instead of ONLY the fixed 20% markup advance, a creator can request a custom
    upfront amount with a reason. The brand approves/rejects; on approval the
    requested amount becomes the escrow advance (and the quote endpoint must be
    re-locked against it before deposit).
    """
    __tablename__ = "advance_requests"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    reason = Column(Text, nullable=True)
    status = Column(String(30), default="pending")  # pending | approved | rejected | superseded
    decided_at = Column(DateTime(timezone=True), nullable=True)
    decision_note = Column(Text, nullable=True)
    deposit_transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    reporter_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(String(30), nullable=False) # profile, post, brief, message
    target_id = Column(String(36), nullable=False)
    reason = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="open") # open, under_review, resolved, dismissed
    reviewed_by = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    actor_id = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    metadata_json = Column(Text, default="{}") # sanitized metadata
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)


# ============================================================
# PHASE 2 — ANONYMOUS CREATOR MARKETPLACE MODELS
# Added: October 2026 | Hypear AI v2.0
# ============================================================

class PIIVault(Base):
    """
    Encrypted identity store — real names/emails/phones are NEVER in plain text.
    Fernet AES-256 encryption via PII_ENCRYPTION_KEY env variable.
    Only the PIIVaultService (admin-gated) can decrypt these values.
    """
    __tablename__ = "pii_vaults"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    real_name_encrypted = Column(Text, nullable=True)       # Fernet-encrypted string
    real_email_encrypted = Column(Text, nullable=True)      # Fernet-encrypted string
    real_phone_encrypted = Column(Text, nullable=True)      # Fernet-encrypted string
    kyc_provider = Column(String(50), nullable=True)        # aadhaar_api | stripe_identity | manual
    kyc_reference = Column(String(100), nullable=True)      # Provider's session / reference ID
    kyc_status = Column(String(30), default="not_started")  # not_started | pending | verified | rejected
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    profile = relationship("Profile", back_populates="pii_vault")


class PIIInterceptEvent(Base):
    """
    Audit log for every PII interception in the chat system.
    Stores SHA-256 hash of the matched value (NOT the actual PII).
    3 violations → account_status = 'pending_review'.
    """
    __tablename__ = "pii_intercept_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
    sender_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    pii_type = Column(String(50), nullable=False)           # phone_india | phone_intl | email | instagram_handle | upi_id | whatsapp_hint | telegram | linkedin
    was_blocked = Column(Boolean, default=True)
    raw_match_hash = Column(String(64), nullable=True)      # SHA-256 of matched value, first 16 chars shown in admin
    detected_at = Column(DateTime(timezone=True), default=utc_now, index=True)


class Dispute(Base):
    """
    Dispute Resolution Workflow.
    Filing a dispute automatically freezes all related escrow transactions.
    Lifecycle: open → under_review → resolved_* | escalated → closed
    """
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filed_by_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    against_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(100), nullable=False)            # non_delivery | quality_dispute | payment_issue | scope_creep | identity_breach
    description = Column(Text, nullable=False)
    evidence_urls = Column(Text, default="[]")              # JSON list of S3 file URLs
    status = Column(String(30), default="open")             # open | under_review | resolved_creator | resolved_brand | escalated | closed
    arbitrator_id = Column(String(36), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    escrow_action = Column(String(30), nullable=True)       # release_to_creator | refund_to_brand | split_50_50
    ai_audit_report = Column(Text, nullable=True)           # JSON string containing autonomous LLM fact-finding & arbitration synthesis
    ai_recommended_action = Column(String(50), nullable=True) # e.g. release_to_creator | refund_to_brand | split_pro_rata
    ai_confidence_score = Column(Float, nullable=True)      # 0.0 - 1.0 confidence score
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project = relationship("Project", foreign_keys=[project_id])
    filed_by = relationship("Profile", foreign_keys=[filed_by_id])
    against = relationship("Profile", foreign_keys=[against_id])
    arbitrator = relationship("Profile", foreign_keys=[arbitrator_id])

    __table_args__ = (
        CheckConstraint("filed_by_id != against_id", name="disallow_self_dispute"),
    )


class ComputeEscrowSession(Base):
    """
    GPU Compute Escrow for Try-Before-You-Buy sandbox.
    Brand locks a compute budget before creator starts work.
    Status: locked → active → completed | expired | refunded
    """
    __tablename__ = "compute_escrow_sessions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    brand_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    brief_id = Column(String(36), ForeignKey("creative_briefs.id", ondelete="SET NULL"), nullable=True)
    gpu_tier = Column(String(20), nullable=False)               # v100 | a100 | h100
    gpu_cost_per_hour_usd = Column(Float, nullable=False)       # 8.0 | 18.0 | 35.0
    allocated_hours = Column(Float, default=1.0)
    used_hours = Column(Float, default=0.0)
    total_locked_usd = Column(Float, nullable=False)
    total_locked_inr = Column(Float, nullable=False, default=0.0)
    payment_reference = Column(String(100), nullable=True)      # Razorpay order ID
    status = Column(String(30), default="locked")               # locked | active | completed | expired | refunded
    started_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    brand = relationship("Profile", foreign_keys=[brand_id])
    creator = relationship("Profile", foreign_keys=[creator_id])


class NDAgreement(Base):
    """
    Non-Disclosure Agreement lifecycle.
    Auto-generated on project award; identity reveal only after both parties sign.
    Signed via DocuSign embed or simple timestamp e-signature.
    """
    __tablename__ = "nda_agreements"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    brand_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    template_version = Column(String(20), default="v1.0")
    brand_signed_at = Column(DateTime(timezone=True), nullable=True)
    creator_signed_at = Column(DateTime(timezone=True), nullable=True)
    brand_ip_hash = Column(String(64), nullable=True)           # SHA-256 of brand signing IP (for legal proof)
    creator_ip_hash = Column(String(64), nullable=True)
    pdf_s3_url = Column(Text, nullable=True)                    # Signed PDF stored in S3
    docusign_envelope_id = Column(String(100), nullable=True)
    status = Column(String(30), default="pending")              # pending | partially_signed | fully_signed | voided
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    project = relationship("Project", foreign_keys=[project_id])
    brand = relationship("Profile", foreign_keys=[brand_id])
    creator = relationship("Profile", foreign_keys=[creator_id])


class CreatorEmbedding(Base):
    """
    OpenAI text-embedding-3-small vectors for semantic creator matching.
    1536-dimensional float arrays stored as JSON.
    Rebuilt on profile update; queried with cosine similarity for brief matching.
    """
    __tablename__ = "creator_embeddings"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    embedding_vector = Column(Text, nullable=False)             # JSON list of 1536 floats
    input_text_hash = Column(String(64), nullable=True)        # SHA-256 of the text that was embedded (change detection)
    model_version = Column(String(50), default="text-embedding-3-small")
    last_updated = Column(DateTime(timezone=True), default=utc_now)

    creator = relationship("Profile", foreign_keys=[creator_id])


class CustomerEnquiry(Base):
    """
    Direct Customer-to-Creator Enquiries & Pitch Requests.
    Synced with enquiries table from CreatorSphere / Supabase schema.
    """
    __tablename__ = "enquiries"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True, index=True)
    brief_id = Column(String(36), ForeignKey("creative_briefs.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(150), nullable=False)
    customer_email = Column(String(200), nullable=False)
    project_title = Column(String(200), nullable=False)
    project_type = Column(String(100), default="Social Video Reel")
    budget_amount = Column(Float, default=5000.0)
    budget_currency = Column(String(10), default="INR")
    duration_seconds = Column(Integer, default=30)
    deadline_days = Column(Integer, default=7)
    scope_details = Column(Text, nullable=False)
    footage_link = Column(Text, nullable=True)
    status = Column(String(30), default="pending") # pending, responded, rejected, converted
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    creator = relationship("Profile", foreign_keys=[creator_id])


class FinancialLedger(Base):
    """
    Double-Entry Financial Audit Ledger conforming to Section 9 of the Master Specification.
    Tracks all escrow holds, fees, releases, and dispute holds.
    """
    __tablename__ = "financial_ledger"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    payment_id = Column(String(36), nullable=False, index=True)
    entry_type = Column(String(50), nullable=False) # payment_received, platform_fee, creator_payout, refund, dispute_hold
    account = Column(String(50), nullable=False)    # escrow_holding, platform_revenue, creator_payable
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    reference_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class ContactUnlock(Base):
    """
    One-sided Creator Contact Unlock record.
    Created automatically when customer advance payment is confirmed.
    """
    __tablename__ = "contact_unlocks"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    customer_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), nullable=True)
    payment_id = Column(String(36), nullable=True)
    status = Column(String(20), default="active") # active, revoked, refunded
    unlocked_at = Column(DateTime(timezone=True), default=utc_now)


class DraftSubmission(Base):
    """
    Creator Draft Submission with Server-Side Dynamic Watermark Protection.
    Before final 70% payment release, brands can only view/download the watermarked rendition.
    """
    __tablename__ = "draft_submissions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_id = Column(String(36), nullable=True)
    version = Column(Integer, default=1)
    title = Column(String(200), nullable=False)
    original_file_path = Column(String(500), nullable=False) # stored securely, inaccessible to brand
    watermarked_file_path = Column(String(500), nullable=False) # watermarked rendition served to brand
    watermark_token = Column(String(100), nullable=False)
    file_type = Column(String(50), default="video") # video | image
    sha256_hash = Column(String(64), nullable=False)
    c2pa_manifest_id = Column(String(100), nullable=True)
    status = Column(String(30), default="under_review") # under_review | approved | changes_requested
    feedback_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now)


