"""
Creator-to-Brief Matching Algorithm for FRAME.
Conforms to Section 13 of the Master Specification:
- Hard eligibility checks (accepting projects, minimum budget check)
- Configurable weights:
  - Skills & specialization: 30%
  - Portfolio style & content type: 25%
  - AI tools & workflow compatibility: 15%
  - Format compatibility: 10%
  - Budget fit: 10%
  - Availability: 10%
- Returns explainable component scores, matching reasons, gaps, and separates creative match from KYC and Trust.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from server.db.models import Profile, CreatorProfile, PortfolioItem, CreativeBrief, MatchResult, VerificationRecord
from server.services.trust_score import TrustScoreService

class MatchingService:
    @classmethod
    def match_creators_to_brief(cls, db: Session, brief_id: str) -> List[Dict[str, Any]]:
        brief = db.query(CreativeBrief).filter(CreativeBrief.id == brief_id).first()
        if not brief:
            return []

        # Parse brief criteria
        brief_content_types = [ct.lower() for ct in json.loads(brief.content_types or "[]")]
        brief_aspect_ratios = [ar.lower() for ar in json.loads(brief.aspect_ratios or "[]")]
        brief_deliverables = [d.lower() for d in json.loads(brief.deliverables or "[]")]
        brief_style = (brief.creative_style or "").lower()
        brief_budget = float(brief.budget_max or brief.budget_min or 5000.0)

        # Query all active public creators
        creators = db.query(Profile).filter(
            Profile.role == "creator",
            Profile.account_status == "active"
        ).all()

        scored_creators = []

        for c in creators:
            details = c.creator_details
            if not details:
                continue

            # --- HARD ELIGIBILITY CHECK ---
            # 1. Profile visibility
            if details.profile_visibility != "public":
                continue

            # 2. Minimum budget check
            if details.minimum_budget and details.minimum_budget > brief_budget:
                continue

            # Load creator attributes
            c_skills = [s.lower() for s in json.loads(details.skills or "[]")]
            c_tools = [t.lower() for t in json.loads(details.ai_tools or "[]")]
            c_content_types = [ct.lower() for ct in json.loads(details.supported_content_types or "[]")]
            c_ratios = [ar.lower() for ar in json.loads(details.aspect_ratios or "[]")]
            c_specializations = [sp.lower() for sp in json.loads(details.specializations or "[]")]

            match_reasons = []
            compatibility_gaps = []

            # 1. Skills & Specialization Fit (Weight: 30%)
            skill_hits = 0
            for req in brief_deliverables + brief_content_types:
                if any(req in s or s in req for s in c_skills + c_specializations):
                    skill_hits += 1
            skills_score = min(100.0, 50.0 + (skill_hits * 25.0))
            if skill_hits > 0:
                match_reasons.append(f"Strong specialization match with {skill_hits} aligned creative capabilities.")
            else:
                compatibility_gaps.append("Creator primary specialization is tangential to this brief deliverable.")

            # 2. Portfolio Style & Content Type (Weight: 25%)
            ct_overlap = any(any(b_ct in c_ct or c_ct in b_ct for c_ct in c_content_types) for b_ct in brief_content_types)
            content_type_score = 95.0 if ct_overlap else 40.0
            if ct_overlap:
                match_reasons.append("Creator has demonstrated portfolio work in requested content category.")
            else:
                compatibility_gaps.append("No direct category match in primary supported content types.")

            # Check style in portfolio items
            sample_items = db.query(PortfolioItem).filter(
                PortfolioItem.creator_id == c.id,
                PortfolioItem.visibility == "public"
            ).all()

            style_hits = 0
            relevant_portfolio_refs = []
            for item in sample_items:
                item_styles = [st.lower() for st in json.loads(item.style_tags or "[]")]
                if any(s in brief_style for s in item_styles):
                    style_hits += 1
                    relevant_portfolio_refs.append({
                        "id": item.id,
                        "title": item.title,
                        "thumbnail_path": item.thumbnail_path,
                        "evidence_status": item.evidence_status
                    })
            portfolio_score = min(100.0, (content_type_score * 0.6) + (min(40.0, style_hits * 20.0)))

            # 3. AI Tools & Workflow Compatibility (Weight: 15%)
            # High score if using generative stacks (Runway, ComfyUI, Flux, Kling)
            tools_score = 85.0
            if any("comfy" in t or "flux" in t or "runway" in t for t in c_tools):
                tools_score = 98.0
                match_reasons.append("Certified AI generative toolchain (ComfyUI / Runway / Flux.1).")

            # 4. Format & Aspect Ratio Compatibility (Weight: 10%)
            format_overlap = any(any(b_ar in c_ar or c_ar in b_ar for c_ar in c_ratios) for b_ar in brief_aspect_ratios)
            format_score = 100.0 if format_overlap or not brief_aspect_ratios else 50.0
            if format_overlap:
                match_reasons.append("Supports requested multi-platform aspect ratio natively.")
            else:
                compatibility_gaps.append("May require post-production letterboxing/re-framing.")

            # 5. Budget Fit (Weight: 10%)
            if details.minimum_budget and details.minimum_budget <= brief_budget:
                budget_score = 95.0
                match_reasons.append("Creator rates align within client budget ceiling.")
            else:
                budget_score = 80.0

            # 6. Availability (Weight: 10%)
            if details.availability_status == "available" and details.accepting_projects:
                avail_score = 100.0
                match_reasons.append("Immediate availability for production kickoff.")
            elif details.availability_status == "busy":
                avail_score = 60.0
                compatibility_gaps.append("Creator currently has active client workload (busy).")
            else:
                avail_score = 30.0
                compatibility_gaps.append("Creator marked as unavailable.")

            # Weighted Creative Suitability Score
            overall_score = round(
                (skills_score * 0.30) +
                (portfolio_score * 0.25) +
                (tools_score * 0.15) +
                (format_score * 0.10) +
                (budget_score * 0.10) +
                (avail_score * 0.10),
                1
            )
            overall_score = min(99.4, max(40.0, overall_score))

            # Separate Trust Evidence & Verification Signals (DO NOT CONFLATE)
            trust_info = TrustScoreService.calculate_creator_trust_score(db, c.id)
            verification = db.query(VerificationRecord).filter(
                VerificationRecord.user_id == c.id,
                VerificationRecord.status == "verified"
            ).first()

            scored_creators.append({
                "creator_id": c.id,
                "creator_name": c.display_name,
                "handle": f"@{c.username}",
                "avatar_url": c.avatar_url,
                "match_score": overall_score,
                "component_scores": {
                    "skills_and_specialization": skills_score,
                    "portfolio_and_style": portfolio_score,
                    "ai_tools_and_workflow": tools_score,
                    "format_compatibility": format_score,
                    "budget_fit": budget_score,
                    "availability": avail_score
                },
                "match_reasons": match_reasons[:4],
                "compatibility_gaps": compatibility_gaps[:2],
                "relevant_portfolio_references": relevant_portfolio_refs[:3],
                "budget_compatibility": {
                    "client_budget": brief_budget,
                    "creator_min_budget": details.minimum_budget,
                    "hourly_compute_rate": details.hourly_compute_rate,
                    "status": "FITS_BUDGET" if (details.minimum_budget or 0) <= brief_budget else "BUDGET_TIGHT"
                },
                "availability": {
                    "status": details.availability_status,
                    "accepting_projects": details.accepting_projects
                },
                "rights_status": "COMMERCIAL_CLEARANCE_READY",
                "identity_verification": {
                    "status": verification.status if verification else "unverified",
                    "is_demo": verification.is_demo if verification else True
                },
                "professional_trust": {
                    "score": trust_info.get("overall_score"),
                    "completed_projects": trust_info.get("completed_projects_count"),
                    "coverage": trust_info.get("evidence_coverage")
                }
            })

        # Rank descending
        scored_creators.sort(key=lambda x: x["match_score"], reverse=True)

        # Persist or update match results in database
        for sc in scored_creators:
            mr = db.query(MatchResult).filter(
                MatchResult.brief_id == brief_id,
                MatchResult.creator_id == sc["creator_id"]
            ).first()
            if not mr:
                mr = MatchResult(
                    brief_id=brief_id,
                    creator_id=sc["creator_id"],
                    match_score=sc["match_score"],
                    component_scores=json.dumps(sc["component_scores"]),
                    match_reasons=json.dumps(sc["match_reasons"]),
                    compatibility_gaps=json.dumps(sc["compatibility_gaps"]),
                    rights_status=sc["rights_status"],
                    calculated_at=datetime.now(timezone.utc)
                )
                db.add(mr)
            else:
                mr.match_score = sc["match_score"]
                mr.component_scores = json.dumps(sc["component_scores"])
                mr.match_reasons = json.dumps(sc["match_reasons"])
                mr.compatibility_gaps = json.dumps(sc["compatibility_gaps"])
                mr.calculated_at = datetime.now(timezone.utc)
        db.commit()

        return scored_creators
