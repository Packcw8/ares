from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List

from db import get_db
from models.user import User
from models.rating import RatedEntity, RatingCategoryScore
from models.evidence import Evidence
from utils.auth import get_current_user
from schemas.rating_schemas import RatedEntityOut
from schemas.entity_admin import AdminEntityUpdate
from datetime import timedelta

router = APIRouter(prefix="/admin", tags=["admin"])


# ======================================================
# 🔐 Role-based dependency
# ======================================================
def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return current_user


# ======================================================
# 👤 USER MANAGEMENT
# ======================================================
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


# ======================================================
# 🏛️ OFFICIAL VERIFICATION
# ======================================================
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
    user.official_verified_at = datetime.now(timezone.utc)
    user.verified_by_admin_id = admin_user.id

    db.commit()
    db.refresh(user)

    return {
        "message": f"Official {user.username} verified successfully.",
        "user_id": user.id,
    }


# ======================================================
# 🏷️ ENTITY MODERATION
# ======================================================
@router.get("/entities/pending", response_model=List[RatedEntityOut])
def get_pending_entities(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    return (
        db.query(RatedEntity)
        .filter(RatedEntity.approval_status == "under_review")
        .order_by(RatedEntity.created_at.desc())
        .all()
    )


@router.post("/entities/{entity_id}/approve", response_model=RatedEntityOut)
def approve_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    entity = db.query(RatedEntity).filter(RatedEntity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity.approval_status = "approved"
    entity.approved_by = admin_user.id
    entity.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entity)
    return entity


@router.post("/entities/{entity_id}/reject", response_model=RatedEntityOut)
def reject_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    entity = db.query(RatedEntity).filter(RatedEntity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity.approval_status = "rejected"
    entity.approved_by = admin_user.id
    entity.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(entity)
    return entity


# ======================================================
# 📂 ALL EVIDENCE (ADMIN)
# ======================================================
@router.get("/evidence")
def get_all_evidence(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Admin-only:
    - List ALL evidence
    - Regardless of flagged status
    - Regardless of entity approval
    """

    evidence = (
        db.query(Evidence)
        .join(RatedEntity, Evidence.entity_id == RatedEntity.id)
        .order_by(Evidence.timestamp.desc())
        .all()
    )

    return [
        {
            "id": e.id,
            "blob_url": e.blob_url,
            "description": e.description,
            "tags": e.tags,
            "location": e.location,
            "is_public": e.is_public,
            "is_anonymous": e.is_anonymous,
            "entity_id": e.entity_id,
            "entity_name": e.entity.name if e.entity else None,
            "entity_status": e.entity.approval_status if e.entity else None,
            "created_at": e.timestamp,
        }
        for e in evidence
    ]


# ======================================================
# 🗑️ DELETE ANY EVIDENCE (ADMIN)
# ======================================================
@router.delete("/evidence/{evidence_id}")
def admin_delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """
    Admin can delete ANY evidence:
    - flagged or not
    - public or private
    - anonymous or user-owned
    """

    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    db.delete(evidence)
    db.commit()

    return {"message": f"Evidence {evidence_id} deleted"}


# ======================================================
# 🔔 ADMIN DASHBOARD COUNTS
# ======================================================
@router.get("/counts")
def admin_counts(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    pending_entities = (
        db.query(func.count(RatedEntity.id))
        .filter(RatedEntity.approval_status == "under_review")
        .scalar()
    )

    flagged_ratings = (
        db.query(func.count(RatingCategoryScore.id))
        .filter(RatingCategoryScore.flagged == True)
        .scalar()
    )

    unverified_ratings = (
        db.query(func.count(RatingCategoryScore.id))
        .filter(RatingCategoryScore.verified == False)
        .scalar()
    )

    flagged_evidence = (
        db.query(func.count(Evidence.id))
        .join(RatedEntity, Evidence.entity_id == RatedEntity.id)
        .filter(
            (Evidence.is_public == True)
            | (RatedEntity.approval_status == "rejected")
        )
        .scalar()
    )

    return {
        "pending_entities": pending_entities or 0,
        "flagged_ratings": flagged_ratings or 0,
        "unverified_ratings": unverified_ratings or 0,
        "flagged_evidence": flagged_evidence or 0,
    }

# ======================================================
# 🔔 Edit Officials
# ======================================================

@router.patch("/entities/{entity_id}")
def admin_update_entity(
    entity_id: int,
    payload: AdminEntityUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    entity = db.query(RatedEntity).filter(RatedEntity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if entity.approval_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Only approved entities may be edited"
        )

    for field, value in payload.dict(exclude_unset=True).items():
        setattr(entity, field, value)

    db.commit()
    db.refresh(entity)

    return {
        "message": "Entity updated successfully",
        "entity_id": entity.id
    }

@router.get("/entities")
def list_all_entities(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    return (
        db.query(RatedEntity)
        .order_by(RatedEntity.created_at.desc())
        .all()
    )

# ======================================================
# 🏷️ ENTITY MODERATION
# ======================================================
@router.post("/entities/{entity_id}/retire")
def retire_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    entity = db.query(RatedEntity).filter(RatedEntity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if entity.approval_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Only approved entities can be retired"
        )

    entity.approval_status = "retired"
    db.commit()

    return {"message": "Entity retired successfully"}

@router.get("/users/new")
def get_new_users(
    days: int = 7,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)

    users = (
        db.query(User)
        .filter(User.created_at >= since)
        .order_by(User.created_at.desc())
        .all()
    )

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_email_verified": u.is_email_verified,
            "is_verified": u.is_verified,
            "created_at": u.created_at,
        }
        for u in users
    ]
