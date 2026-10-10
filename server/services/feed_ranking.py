"""
Feed Ranking Algorithm for FRAME.
Conforms to Section 10 of the Master Specification:
- Preference & category relevance: 35%
- Followed creators & saved-content relevance: 25%
- Recency: 20%
- Content completeness & quality signals: 10%
- Discovery diversity: 10%
- Filters out private, removed, and restricted content before ranking
- Diversity rule avoids showing excessive consecutive posts from same creator
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from server.db.models import FeedPost, Follow, Save, Like, Profile, CreatorProfile

class FeedRankingService:
    @classmethod
    def get_ranked_feed(
        cls, 
        db: Session, 
        current_user_id: Optional[str] = None,
        category_preference: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        # 1. Fetch only eligible posts (public, approved)
        posts = db.query(FeedPost).filter(
            FeedPost.visibility == "public",
            FeedPost.moderation_status == "approved"
        ).order_by(FeedPost.published_at.desc()).all()

        if not posts:
            return []

        # 2. Gather user context signals if authenticated
        followed_creator_ids = set()
        saved_post_ids = set()
        liked_post_ids = set()

        if current_user_id:
            follows = db.query(Follow).filter(Follow.follower_id == current_user_id).all()
            followed_creator_ids = {f.followed_id for f in follows}
            saves = db.query(Save).filter(Save.user_id == current_user_id).all()
            saved_post_ids = {s.post_id for s in saves}
            likes = db.query(Like).filter(Like.user_id == current_user_id).all()
            liked_post_ids = {l.post_id for l in likes}

        now = datetime.now(timezone.utc)
        scored_posts = []

        for p in posts:
            # Signal 1: Category Relevance (Weight: 35%)
            p_styles = [st.lower() for st in json.loads(p.style_tags or "[]")]
            p_content_type = p.content_type.lower()
            cat_score = 50.0
            if category_preference and category_preference.lower() != "all":
                pref = category_preference.lower()
                if pref in p_content_type or any(pref in s for s in p_styles):
                    cat_score = 100.0
                else:
                    cat_score = 30.0

            # Signal 2: Followed & Saved Signals (Weight: 25%)
            rel_score = 40.0
            if p.creator_id in followed_creator_ids:
                rel_score += 40.0
            if p.id in saved_post_ids:
                rel_score += 20.0
            rel_score = min(100.0, rel_score)

            # Signal 3: Recency (Weight: 20%)
            pub_date = p.published_at or p.created_at or now
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)
            age_hours = max(0.1, (now - pub_date).total_seconds() / 3600.0)
            recency_score = max(20.0, 100.0 - (age_hours * 1.5))

            # Signal 4: Content Completeness & Quality (Weight: 10%)
            quality_score = 60.0
            if p.thumbnail_path and p.media_path:
                quality_score += 20.0
            if len(p_styles) >= 2:
                quality_score += 10.0
            if p.caption and len(p.caption) > 20:
                quality_score += 10.0
            quality_score = min(100.0, quality_score)

            # Signal 5: Discovery Diversity (Weight: 10%)
            # Higher initial score for fresh discoveries not yet followed
            diversity_score = 90.0 if p.creator_id not in followed_creator_ids else 50.0

            # Final Score Calculation
            final_score = (
                (cat_score * 0.35) +
                (rel_score * 0.25) +
                (recency_score * 0.20) +
                (quality_score * 0.10) +
                (diversity_score * 0.10)
            )

            # Fetch creator profile
            creator_profile = db.query(Profile).filter(Profile.id == p.creator_id).first()
            creator_details = db.query(CreatorProfile).filter(CreatorProfile.user_id == p.creator_id).first()

            # Likes & saves count
            like_count = db.query(Like).filter(Like.post_id == p.id).count()
            save_count = db.query(Save).filter(Save.post_id == p.id).count()

            scored_posts.append({
                "post": p,
                "score": final_score,
                "creator": creator_profile,
                "creator_details": creator_details,
                "like_count": like_count,
                "save_count": save_count,
                "is_liked": p.id in liked_post_ids,
                "is_saved": p.id in saved_post_ids,
                "is_following": p.creator_id in followed_creator_ids
            })

        # Rank descending
        scored_posts.sort(key=lambda x: x["score"], reverse=True)

        # Apply Diversity Re-ranking (prevent > 2 consecutive posts from the same creator)
        diversified = []
        creator_consecutive_count: Dict[str, int] = {}
        deferred = []

        for item in scored_posts:
            cid = item["post"].creator_id
            if creator_consecutive_count.get(cid, 0) < 2:
                diversified.append(item)
                creator_consecutive_count[cid] = creator_consecutive_count.get(cid, 0) + 1
            else:
                deferred.append(item)

        diversified.extend(deferred)

        # Serialize results
        results = []
        for d in diversified[offset:offset + limit]:
            p = d["post"]
            c = d["creator"]
            cd = d["creator_details"]
            results.append({
                "id": p.id,
                "creator_id": p.creator_id,
                "creator_name": c.display_name if c else "AI Creator",
                "creator_handle": f"@{c.username}" if c else "@creator",
                "creator_avatar": c.avatar_url if c else None,
                "caption": p.caption,
                "media_path": p.media_path,
                "thumbnail_path": p.thumbnail_path,
                "content_type": p.content_type,
                "style_tags": json.loads(p.style_tags or "[]"),
                "ai_tools": json.loads(p.ai_tools or "[]"),
                "ai_models": json.loads(p.ai_models or "[]"),
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "ranking_score": round(d["score"], 2),
                "likes_count": d["like_count"],
                "saves_count": d["save_count"],
                "is_liked": d["is_liked"],
                "is_saved": d["is_saved"],
                "is_following": d["is_following"]
            })

        return results
