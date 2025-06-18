from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.official_post import OfficialPost
from models.user import User
from schemas.official_post_schemas import OfficialPostCreate, OfficialPostOut
from utils.auth import get_current_user

router = APIRouter(prefix="/forum", tags=["official_posts"])

# ✅ Create a post (official or admin only)
@router.post("/create", response_model=OfficialPostOut)
def create_post(
    post: OfficialPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_official and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only officials can post")

    new_post = OfficialPost(
        title=post.title,
        body=post.body,
        author_id=current_user.id,
        entity_id=post.entity_id,
        verified=True
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# ✅ Get all posts
@router.get("/", response_model=list[OfficialPostOut])
def list_posts(db: Session = Depends(get_db)):
    return db.query(OfficialPost).order_by(OfficialPost.created_at.desc()).all()

# ✅ Get single post
@router.get("/{post_id}", response_model=OfficialPostOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(OfficialPost).filter(OfficialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
