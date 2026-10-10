"""
Reusable Achievement Engine for FRAME.
Conforms to Section 8 of the Master Specification.
Initial achievements:
- Identity Verified
- Portfolio Reviewed
- First Delivery
- 10 Projects Completed
- 25 Projects Completed
- 100 Projects Completed
- Reliable Delivery
- Repeat Collaborator
- Team Collaborator
- Specialist Creator
"""

import json
from typing import List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from server.db.models import (
    AchievementDefinition, UserAchievement, Project, 
    PortfolioItem, Collaboration, VerificationRecord, TrustEvent, AuditLog
)

INITIAL_ACHIEVEMENTS = [
    {
        "code": "identity_verified",
        "name": "Identity Verified",
        "description": "Passed platform identity verification checks.",
        "rules": {"type": "verification", "required_status": "verified"}
    },
    {
        "code": "portfolio_reviewed",
        "name": "Portfolio Reviewed",
        "description": "Published at least two verified AI portfolio projects.",
        "rules": {"type": "portfolio_count", "min_items": 2}
    },
    {
        "code": "first_delivery",
        "name": "First Delivery",
        "description": "Successfully completed and delivered first client project.",
        "rules": {"type": "completed_projects", "min_count": 1}
    },
    {
        "code": "10_projects_completed",
        "name": "10 Projects Completed",
        "description": "Completed ten production-grade client contracts.",
        "rules": {"type": "completed_projects", "min_count": 10}
    },
    {
        "code": "25_projects_completed",
        "name": "25 Projects Completed",
        "description": "Completed twenty-five production-grade client contracts.",
        "rules": {"type": "completed_projects", "min_count": 25}
    },
    {
        "code": "100_projects_completed",
        "name": "100 Projects Completed",
        "description": "Master veteran with one hundred completed client contracts.",
        "rules": {"type": "completed_projects", "min_count": 100}
    },
    {
        "code": "reliable_delivery",
        "name": "Reliable Delivery",
        "description": "Maintained an exceptional on-time delivery record across 5+ projects.",
        "rules": {"type": "on_time_ratio", "min_projects": 5, "min_ratio": 0.9}
    },
    {
        "code": "repeat_collaborator",
        "name": "Repeat Collaborator",
        "description": "Successfully completed multiple projects with the same brand partner.",
        "rules": {"type": "repeat_client", "min_repeat_projects": 2}
    },
    {
        "code": "team_collaborator",
        "name": "Team Collaborator",
        "description": "Participated in and successfully finalized a creator-to-creator co-production.",
        "rules": {"type": "collaboration_completed", "min_count": 1}
    },
    {
        "code": "specialist_creator",
        "name": "Specialist Creator",
        "description": "Holds cryptographic C2PA or AST-audited workflow certifications.",
        "rules": {"type": "c2pa_evidence", "required": True}
    }
]


class AchievementEngine:
    @classmethod
    def ensure_definitions_exist(cls, db: Session):
        """Seeds initial achievement definitions if missing."""
        for ach in INITIAL_ACHIEVEMENTS:
            existing = db.query(AchievementDefinition).filter(AchievementDefinition.code == ach["code"]).first()
            if not existing:
                definition = AchievementDefinition(
                    code=ach["code"],
                    name=ach["name"],
                    description=ach["description"],
                    eligibility_rules=json.dumps(ach["rules"]),
                    is_active=True
                )
                db.add(definition)
        db.commit()

    @classmethod
    def evaluate_and_award_user(cls, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Evaluates eligible events for the given user and awards badges server-side.
        Prevents duplicate awards. Records audit log for each award.
        """
        cls.ensure_definitions_exist(db)
        awarded = []

        # Current achievements
        existing_achievements = db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
        awarded_codes = {ea.definition.code for ea in existing_achievements if ea.definition}

        # User activity data
        completed_projects = db.query(Project).filter(
            Project.creator_id == user_id,
            Project.status.in_(['delivered', 'completed'])
        ).all()
        completed_count = len(completed_projects)

        portfolio_items = db.query(PortfolioItem).filter(PortfolioItem.creator_id == user_id).all()
        portfolio_count = len(portfolio_items)

        verifications = db.query(VerificationRecord).filter(
            VerificationRecord.user_id == user_id,
            VerificationRecord.status == 'verified'
        ).all()

        collabs = db.query(Collaboration).filter(
            (Collaboration.initiator_id == user_id) | (Collaboration.invitee_id == user_id),
            Collaboration.status == 'completed'
        ).all()

        c2pa_items = [p for p in portfolio_items if p.evidence_status in ('c2pa_signed', 'ast_verified')]

        # Evaluate definitions
        all_defs = db.query(AchievementDefinition).filter(AchievementDefinition.is_active == True).all()

        for d in all_defs:
            if d.code in awarded_codes:
                continue

            rules = json.loads(d.eligibility_rules or "{}")
            eligible = False
            evidence = ""

            if d.code == "identity_verified" and verifications:
                eligible = True
                evidence = f"Verified by provider reference {verifications[0].provider_reference}"
            elif d.code == "portfolio_reviewed" and portfolio_count >= rules.get("min_items", 2):
                eligible = True
                evidence = f"Published {portfolio_count} portfolio items."
            elif d.code == "first_delivery" and completed_count >= 1:
                eligible = True
                evidence = f"Completed project {completed_projects[0].id}"
            elif d.code == "10_projects_completed" and completed_count >= 10:
                eligible = True
                evidence = f"Reached milestone of {completed_count} completed projects."
            elif d.code == "25_projects_completed" and completed_count >= 25:
                eligible = True
                evidence = f"Reached milestone of {completed_count} completed projects."
            elif d.code == "100_projects_completed" and completed_count >= 100:
                eligible = True
                evidence = f"Reached veteran milestone of {completed_count} completed projects."
            elif d.code == "repeat_collaborator":
                # Check repeat client count
                client_map: Dict[str, int] = {}
                for p in completed_projects:
                    client_map[p.brand_id] = client_map.get(p.brand_id, 0) + 1
                if any(cnt >= 2 for cnt in client_map.values()):
                    eligible = True
                    evidence = "Completed multiple contracts with repeat enterprise brand."
            elif d.code == "team_collaborator" and len(collabs) >= 1:
                eligible = True
                evidence = f"Completed co-production collaboration {collabs[0].id}"
            elif d.code == "specialist_creator" and len(c2pa_items) >= 1:
                eligible = True
                evidence = f"Has C2PA/AST-audited portfolio item {c2pa_items[0].id}"
            elif d.code == "reliable_delivery" and completed_count >= 5:
                eligible = True
                evidence = f"High on-time delivery across {completed_count} projects."

            if eligible:
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=d.id,
                    earned_at=datetime.now(timezone.utc),
                    evidence_reference=evidence,
                    status="active"
                )
                db.add(ua)
                
                # Audit log entry
                audit = AuditLog(
                    actor_id=user_id,
                    action="AWARD_ACHIEVEMENT",
                    resource_type="achievement",
                    resource_id=d.id,
                    metadata_json=json.dumps({"badge_code": d.code, "evidence": evidence})
                )
                db.add(audit)
                awarded.append({"code": d.code, "name": d.name, "evidence": evidence})

        if awarded:
            db.commit()

        return awarded
