from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.post_comment import PostComment
from models.user import User
from schemas.post_comment_schemas import PostCommentCreate, PostCommentOut
from utils.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])

# ✅ Submit a comment
@router.post("/", response_model=PostCommentOut)
def create_comment(
    comment: PostCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_comment = PostComment(
        post_id=comment.post_id,
        user_id=current_user.id,
        content=comment.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# ✅ Get all comments for a post
@router.get("/post/{post_id}", response_model=list[PostCommentOut])
def get_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    return db.query(PostComment).filter(PostComment.post_id == post_id).order_by(PostComment.created_at.asc()).all()
