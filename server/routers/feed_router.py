"""
Feed, Reels, Likes, Saves, and Follows Router for FRAME.
Conforms to Sections 4, 10 of the Master Specification.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.db.session import get_db
from server.db.models import FeedPost, Like, Save, Follow, Profile
from server.services.feed_ranking import FeedRankingService
from server.services.auth_service import get_current_user_optional, get_current_user

router = APIRouter(prefix="/api/feed", tags=["Feed & Social"])

@router.get("")
def get_feed(
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Optional[Profile] = Depends(get_current_user_optional)
):
    """Returns algorithmically ranked, diversified feed posts."""
    user_id = current_user.id if current_user else None
    ranked_posts = FeedRankingService.get_ranked_feed(
        db=db,
        current_user_id=user_id,
        category_preference=category,
        limit=limit,
        offset=offset
    )
    return {"feed": ranked_posts}

@router.post("/{post_id}/like")
def toggle_like(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Toggles like on a post with database unique constraint."""
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    existing_like = db.query(Like).filter(Like.user_id == current_user.id, Like.post_id == post_id).first()
    if existing_like:
        db.delete(existing_like)
        db.commit()
        liked = False
    else:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.add(new_like)
        db.commit()
        liked = True

    count = db.query(Like).filter(Like.post_id == post_id).count()
    return {"liked": liked, "likes_count": count}

@router.post("/{post_id}/save")
def toggle_save(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Toggles save/bookmark on a post with database unique constraint."""
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    existing_save = db.query(Save).filter(Save.user_id == current_user.id, Save.post_id == post_id).first()
    if existing_save:
        db.delete(existing_save)
        db.commit()
        saved = False
    else:
        new_save = Save(user_id=current_user.id, post_id=post_id)
        db.add(new_save)
        db.commit()
        saved = True

    count = db.query(Save).filter(Save.post_id == post_id).count()
    return {"saved": saved, "saves_count": count}

@router.post("/follow/{target_user_id}")
def toggle_follow(
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user)
):
    """Follows or unfollows a creator. Strictly prevents self-following."""
    if current_user.id == target_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself.")

    target = db.query(Profile).filter(Profile.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")

    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.followed_id == target_user_id
    ).first()

    if existing_follow:
        db.delete(existing_follow)
        db.commit()
        following = False
    else:
        new_follow = Follow(follower_id=current_user.id, followed_id=target_user_id)
        db.add(new_follow)
        db.commit()
        following = True

    count = db.query(Follow).filter(Follow.followed_id == target_user_id).count()
    return {"following": following, "followers_count": count}
