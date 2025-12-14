from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from db import get_db
from models.official_post import OfficialPost
from models.user import User
from utils.auth import get_current_user
from schemas.official_post_schemas import OfficialPostCreate

router = APIRouter(prefix="/forum", tags=["official_posts"])


# ✅ Create a post (official_verified or admin only)
@router.post("/create")
def create_post(
    post: OfficialPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("official_verified", "admin"):
        raise HTTPException(status_code=403, detail="Only officials can post")

    new_post = OfficialPost(
        title=post.title,
        body=post.body,
        author_id=current_user.id,
        entity_id=post.entity_id,
        verified=True,
        is_pinned=post.is_pinned,
        is_ama=post.is_ama,
        tags=post.tags,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


# ✅ Get all posts (forum feed)
@router.get("/")
def list_posts(db: Session = Depends(get_db)):
    posts = (
        db.query(OfficialPost)
        .options(
            joinedload(OfficialPost.entity),
            joinedload(OfficialPost.comments),
        )
        .order_by(OfficialPost.created_at.desc())
        .all()
    )

    return [
        {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "created_at": post.created_at,
            "is_pinned": post.is_pinned,
            "is_ama": post.is_ama,
            "tags": post.tags,
            "verified": post.verified,
            "entity": {
                "id": post.entity.id,
                "name": post.entity.name,
                "state": post.entity.state,
                "county": post.entity.county,
                "type": post.entity.type,
            } if post.entity else None,
            "comment_count": len(post.comments),
        }
        for post in posts
    ]


# ✅ Get single post
@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = (
        db.query(OfficialPost)
        .options(
            joinedload(OfficialPost.entity),
            joinedload(OfficialPost.comments),
        )
        .filter(OfficialPost.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "id": post.id,
        "title": post.title,
        "body": post.body,
        "created_at": post.created_at,
        "is_pinned": post.is_pinned,
        "is_ama": post.is_ama,
        "tags": post.tags,
        "verified": post.verified,
        "entity": {
            "id": post.entity.id,
            "name": post.entity.name,
            "state": post.entity.state,
            "county": post.entity.county,
            "type": post.entity.type,
        } if post.entity else None,
        "comments": [
            {
                "id": c.id,
                "content": c.content,
                "created_at": c.created_at,
                "user_id": c.user_id,
            }
            for c in post.comments
        ],
    }
