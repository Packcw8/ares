from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from db import get_db
from models.user import User
from utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


# 🔐 Role-based dependency
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user


# =========================
# 👤 USER MANAGEMENT
# =========================

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    users = db.query(User).order_by(User.id.desc()).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_verified": user.is_verified,
            "is_email_verified": user.is_email_verified,
        }
        for user in users
    ]


@router.delete("/delete-user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} deleted successfully."}


# =========================
# 🏛️ OFFICIAL VERIFICATION
# =========================

# 📋 List pending officials
@router.get("/officials/pending")
def get_pending_officials(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    officials = (
        db.query(User)
        .filter(User.role == "official_pending")
        .order_by(User.id.desc())
        .all()
    )

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "title": user.title,
            "agency": user.agency,
            "state": user.state,
            "jurisdiction": user.jurisdiction,
            "is_email_verified": user.is_email_verified,
        }
        for user in officials
    ]


# ✅ Verify an official
@router.patch("/officials/{user_id}/verify")
def verify_official(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "official_pending":
        raise HTTPException(
            status_code=400,
            detail="User is not pending official verification",
        )

    user.role = "official_verified"
    user.is_verified = True
    user.official_verified_at = datetime.utcnow()
    user.verified_by_admin_id = admin_user.id

    db.commit()
    db.refresh(user)

    return {
        "message": f"Official {user.username} verified successfully.",
        "user_id": user.id,
    }


# =========================
# 🔎 LEGACY ROUTES (REMOVED / UPDATED)
# =========================
# ❌ Removed:
# - /verify-user/{id}      (expected role='official', no longer exists)
# - /unverified-officials (expected role='official', replaced by official_pending)
#
# These routes could NEVER return data with the new role system
# and would silently break admin verification.
