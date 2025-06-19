from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

# Role-based dependency
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user

@router.patch("/verify-user/{user_id}")
def verify_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != "official":
        raise HTTPException(status_code=400, detail="Only officials can be verified")

    user.is_verified = True
    db.commit()
    return {"message": f"User {user.username} verified successfully."}

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified
        }
        for user in users
    ]


@router.delete("/delete-user/{user_id}")
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully."}

@router.get("/unverified-officials")
def get_unverified_officials(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    officials = db.query(User).filter(User.role == "official", User.is_verified == False).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified
        }
        for user in officials
    ]
