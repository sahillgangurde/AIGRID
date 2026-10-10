"""
Deterministic and Explainable Trust-Score Engine for FRAME.
Conforms to Section 9 of the Master Specification:
- Completion reliability: 35%
- On-time delivery: 25%
- Repeat-client rate: 20%
- Documented outcome reliability: 20%
- Cold-start handling: Minimum evidence threshold with neutral prior (does not penalize new creators)
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from server.db.models import Project, TrustEvent

MINIMUM_EVIDENCE_PROJECTS = 3
NEUTRAL_PRIOR_SCORE = 80.0

class TrustScoreService:
    @classmethod
    def calculate_creator_trust_score(cls, db: Session, creator_id: str) -> Dict[str, Any]:
        """
        Calculates deterministic and explainable trust score from verified database events.
        """
        # Fetch completed or in-progress projects for creator
        projects = db.query(Project).filter(Project.creator_id == creator_id).all()
        completed_projects = [p for p in projects if p.status in ('delivered', 'completed')]
        completed_count = len(completed_projects)

        # Fetch trust events
        trust_events = db.query(TrustEvent).filter(
            TrustEvent.creator_id == creator_id,
            TrustEvent.event_status == 'verified'
        ).all()

        # Check evidence threshold
        if completed_count < MINIMUM_EVIDENCE_PROJECTS:
            return {
                "overall_score": NEUTRAL_PRIOR_SCORE,
                "status": "INSUFFICIENT_EVIDENCE",
                "is_eligible": False,
                "insufficient_data": True,
                "evidence_coverage": round((completed_count / MINIMUM_EVIDENCE_PROJECTS) * 100, 1),
                "completed_projects_count": completed_count,
                "component_scores": {
                    "completion_reliability": NEUTRAL_PRIOR_SCORE,
                    "on_time_delivery": NEUTRAL_PRIOR_SCORE,
                    "repeat_client_rate": NEUTRAL_PRIOR_SCORE,
                    "documented_outcome_reliability": NEUTRAL_PRIOR_SCORE
                },
                "explanation": (
                    f"Creator has completed {completed_count}/{MINIMUM_EVIDENCE_PROJECTS} required projects. "
                    "Assigned a neutral baseline prior. The platform does not penalize creators with limited work history."
                ),
                "is_demo": True,
                "last_calculated_at": datetime.now(timezone.utc).isoformat()
            }

        # 1. Completion Reliability (Weight: 35%)
        # Ratio of successfully delivered projects vs cancelled/disputed
        non_draft_projects = [p for p in projects if p.status not in ('draft', 'contacted')]
        total_undertaken = max(1, len(non_draft_projects))
        cancelled_or_disputed = [p for p in non_draft_projects if p.status in ('cancelled', 'disputed')]
        completion_ratio = max(0.0, 1.0 - (len(cancelled_or_disputed) / total_undertaken))
        completion_score = round(completion_ratio * 100.0, 1)

        # 2. On-Time Delivery (Weight: 25%)
        # Checked against deadlines or trust events
        on_time_events = [e for e in trust_events if e.event_type == 'project_completed_on_time']
        late_events = [e for e in trust_events if e.event_type == 'project_completed_late']
        total_time_evaluated = len(on_time_events) + len(late_events)
        if total_time_evaluated > 0:
            on_time_score = round((len(on_time_events) / total_time_evaluated) * 100.0, 1)
        else:
            on_time_score = 92.0 # Standard positive baseline when on-time records are clean

        # 3. Repeat Client Rate (Weight: 20%)
        # Unique clients with > 1 project
        client_counts: Dict[str, int] = {}
        for p in completed_projects:
            client_counts[p.brand_id] = client_counts.get(p.brand_id, 0) + 1
        repeat_clients = sum(1 for c, count in client_counts.items() if count > 1)
        unique_clients = max(1, len(client_counts))
        repeat_ratio = min(1.0, repeat_clients / (unique_clients * 0.4)) # 40% repeat clients yields 100 score
        repeat_score = round(repeat_ratio * 100.0, 1)

        # 4. Documented Outcome Reliability (Weight: 20%)
        # Sealed C2PA or AST milestones verified without dispute
        disputes = [e for e in trust_events if e.event_type == 'client_dispute_filed']
        sealed_events = [e for e in trust_events if e.event_type == 'documented_milestone_sealed']
        dispute_penalty = min(50.0, len(disputes) * 25.0)
        documented_score = round(max(30.0, 100.0 - dispute_penalty + min(15.0, len(sealed_events) * 3.0)), 1)

        # Overall Weighted Score (35% + 25% + 20% + 20%)
        overall = round(
            (completion_score * 0.35) +
            (on_time_score * 0.25) +
            (repeat_score * 0.20) +
            (documented_score * 0.20),
            1
        )
        overall = min(99.9, max(20.0, overall))

        return {
            "overall_score": overall,
            "status": "VERIFIED_TRACK_RECORD",
            "is_eligible": True,
            "insufficient_data": False,
            "evidence_coverage": 100.0,
            "completed_projects_count": completed_count,
            "component_scores": {
                "completion_reliability": completion_score,
                "on_time_delivery": on_time_score,
                "repeat_client_rate": repeat_score,
                "documented_outcome_reliability": documented_score
            },
            "weights": {
                "completion_reliability": 0.35,
                "on_time_delivery": 0.25,
                "repeat_client_rate": 0.20,
                "documented_outcome_reliability": 0.20
            },
            "explanation": (
                f"Calculated from {completed_count} completed projects: "
                f"Completion Reliability {completion_score}%, On-Time Delivery {on_time_score}%, "
                f"Repeat-Client Rate {repeat_score}%, and Documented Outcomes {documented_score}%."
            ),
            "is_demo": True,
            "last_calculated_at": datetime.now(timezone.utc).isoformat()
        }
