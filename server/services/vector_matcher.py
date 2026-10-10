"""
1024-Dimensional Multi-Modal Style & Moodboard Matching Engine.
Calculates visual centroid embeddings and cosine similarity against indexed creator portfolios.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import hashlib
from server.data.creators_data import CREATORS_DATABASE, generate_deterministic_vector

class VectorMatcherService:
    @staticmethod
    def compute_tag_or_image_vector(input_token: str, dim: int = 1024) -> np.ndarray:
        """
        Generates a 1024-d normalized embedding representation for a given prompt or image token.
        """
        # Hash to deterministic pseudo-random seed
        seed = int(hashlib.sha256(input_token.encode()).hexdigest()[:8], 16)
        vec = np.array(generate_deterministic_vector(seed, dim))
        return vec

    @classmethod
    def match_moodboard(
        cls,
        tags: List[str],
        image_seeds: Optional[List[str]] = None,
        target_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Combines multi-modal inputs into a centroid vector and computes cosine similarity.
        """
        tokens = list(tags)
        if image_seeds:
            tokens.extend([f"img_seed_{s}" for s in image_seeds])

        if not tokens:
            tokens = ["cyberpunk", "cinematic", "lighting"]

        # Calculate Centroid Vector
        vectors = [cls.compute_tag_or_image_vector(t) for t in tokens]
        stacked = np.stack(vectors, axis=0)
        centroid = np.mean(stacked, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 1e-6:
            centroid = centroid / norm

        results = []
        for creator in CREATORS_DATABASE:
            creator_vec = np.array(creator["vector_embedding"])
            # Cosine similarity between unit vectors is dot product
            raw_cosine = float(np.dot(centroid, creator_vec))
            # Rescale into an intuitive 65% - 98% aesthetic similarity range
            similarity_pct = round(65.0 + (raw_cosine + 1.0) * 16.5, 1)
            similarity_pct = min(99.4, max(52.0, similarity_pct))

            # Dynamic aesthetic radar breakdown
            base_radar = creator.get("radar_scores", {})
            radar_breakdown = {
                "palette_match": min(99, int(base_radar.get("palette", 90) * (similarity_pct / 100.0) + 8)),
                "lighting_coherence": min(99, int(base_radar.get("lighting", 92) * (similarity_pct / 100.0) + 6)),
                "structural_depth": min(99, int(base_radar.get("structure", 94) * (similarity_pct / 100.0) + 5)),
                "aesthetic_originality": min(99, int(base_radar.get("originality", 91) * (similarity_pct / 100.0) + 7))
            }

            results.append({
                "creator_id": creator["id"],
                "creator_name": creator["name"],
                "handle": creator["handle"],
                "avatar": creator["avatar"],
                "specialty": creator["specialty"],
                "rating": creator["rating"],
                "verified": creator["verified"],
                "compliance_tier": creator["compliance_tier"],
                "human_likeness": creator["human_likeness"],
                "hourly_compute_rate": creator["hourly_compute_rate"],
                "similarity_score": similarity_pct,
                "radar_breakdown": radar_breakdown,
                "sample_works": creator["sample_works"],
                "base_model": creator["base_model"],
                "style_tags": creator["style_tags"]
            })

        # Rank descending by similarity score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "query_tokens": tokens,
            "vector_dimension": 1024,
            "centroid_norm": round(float(np.linalg.norm(centroid)), 4),
            "top_matches": results
        }
