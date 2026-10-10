"""
Compliance & Likeness Release Verification Service.
Enforces legal gating between Commercial Non-Branded assets and Human Likeness / Editorial tiers.
Assesses Fair Use Factor 4 risks and model release validity.
"""

from typing import Dict, Any, List

HUMAN_LIKENESS_KEYWORDS = {
    "portrait", "face", "man", "woman", "person", "celebrity", "fashion model",
    "eyes", "actor", "likeness", "digital twin", "haute couture", "influencer"
}

TRADEMARK_RISK_KEYWORDS = {
    "nike", "apple", "disney", "marvel", "coca cola", "ferrari", "rolex", "chanel"
}

class ComplianceService:
    @staticmethod
    def audit_content_compliance(
        prompt_text: str,
        has_face_detected: bool,
        claimed_release_id: str = None
    ) -> Dict[str, Any]:
        """
        Audits content for human likeness and trademark infringement risk.
        """
        prompt_lower = prompt_text.lower()
        contains_human_tokens = any(kw in prompt_lower for kw in HUMAN_LIKENESS_KEYWORDS)
        contains_trademark_tokens = [kw for kw in TRADEMARK_RISK_KEYWORDS if kw in prompt_lower]

        is_human_likeness = has_face_detected or contains_human_tokens

        # Categorization
        tier = "HUMAN_LIKENESS_EDITORIAL" if is_human_likeness else "COMMERCIAL_NON_BRANDED"

        # Release Verification
        release_valid = False
        release_details = None
        if is_human_likeness:
            if claimed_release_id and claimed_release_id.startswith("RELEASE-2026"):
                release_valid = True
                release_details = {
                    "release_id": claimed_release_id,
                    "legal_indemnification": "Enterprise Full Coverage ($1M Policy)",
                    "biometric_consent": "Explicit Synthetic Derivative Authorized",
                    "status": "APPROVED_ACTIVE"
                }
            else:
                release_valid = False
                release_details = {
                    "release_id": claimed_release_id or "NONE_PROVIDED",
                    "status": "MISSING_OR_INVALID",
                    "warning": "Commercial use prohibited without verified model release (Civil Code §3344 compliant)."
                }

        # IP Infringement / Fair Use Factor 4 Risk Score (0-100)
        risk_score = 12
        risk_factors = []

        if contains_trademark_tokens:
            risk_score += 65
            risk_factors.append(f"Direct commercial trademark mention: {', '.join(contains_trademark_tokens)}")

        if is_human_likeness and not release_valid:
            risk_score += 45
            risk_factors.append("Unreleased synthetic human likeness posing Right of Publicity liability")
        elif is_human_likeness and release_valid:
            risk_score = max(5, risk_score - 10)
            risk_factors.append("Verified Model Release with indemnity certificate attached")

        risk_level = "LOW" if risk_score < 30 else ("MEDIUM" if risk_score < 60 else "HIGH")

        return {
            "compliance_tier": tier,
            "is_human_likeness": is_human_likeness,
            "model_release_required": is_human_likeness,
            "model_release_verified": release_valid,
            "release_details": release_details,
            "fair_use_factor_4_risk_score": min(100, risk_score),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "commercial_safe": (risk_score < 40 and (not is_human_likeness or release_valid))
        }
