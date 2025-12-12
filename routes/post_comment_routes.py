from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models.post_comment import PostComment
from models.user import User
from schemas.post_comment_schemas import PostCommentCreate, PostCommentOut
from utils.auth import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])


# ======================================================
# CREATE COMMENT (LOGIN REQUIRED)
# ======================================================
@router.post("/", response_model=PostCommentOut)
def create_comment(
    comment: PostCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_comment = PostComment(
        post_id=comment.post_id,
        user_id=current_user.id,
        content=comment.content,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


# ======================================================
# GET COMMENTS FOR A POST (PUBLIC)
# ======================================================
@router.get("/post/{post_id}", response_model=list[PostCommentOut])
def get_comments_for_post(post_id: int, db: Session = Depends(get_db)):
    return (
        db.query(PostComment)
        .filter(PostComment.post_id == post_id)
        .order_by(PostComment.created_at.asc())
        .all()
    )


# ======================================================
# DELETE COMMENT (OWNER ONLY)
# ======================================================
@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(PostComment).filter(PostComment.id == comment_id).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")

    db.delete(comment)
    db.commit()
    return
