from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone

from db import get_db
from models.rating import RatedEntity, RatingCategoryScore, EvidenceAttachment
from models.user import User
from utils.auth import get_current_user
from schemas.rating_schemas import (
    RatedEntityCreate,
    RatedEntityOut,
    RatingCategoryScoreCreate,
    RatingCategoryScoreOut,
    EvidenceAttachmentCreate,
    EvidenceAttachmentOut,
    FlagRequest,
)

router = APIRouter(prefix="/ratings", tags=["ratings"])


# ======================================================
# Recalculate reputation (authoritative)
# ======================================================
def recalculate_reputation(entity_id: int, db: Session) -> float:
    scores = (
        db.query(RatingCategoryScore)
        .filter(RatingCategoryScore.entity_id == entity_id)
        .all()
    )

    if not scores:
        return 100.0

    total = 0.0
    for s in scores:
        avg = (
            s.accountability
            + s.respect
            + s.effectiveness
            + s.transparency
            + s.public_impact
        ) / 5

        weight = 2.5 if s.verified else 1.5
        total += (avg - 5) * weight

    return max(0.0, 100.0 + total)


# ======================================================
# Create Rated Entity
# - Admin: approved immediately
# - Everyone else: under_review
# ======================================================
@router.post("/entities", response_model=RatedEntityOut)
def create_entity(
    entity: RatedEntityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(RatedEntity).filter(
        func.lower(RatedEntity.name) == entity.name.strip().lower(),
        RatedEntity.type == entity.type,
        RatedEntity.state == entity.state,
        RatedEntity.county == entity.county,
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Entity already exists with same name, type, state, and county.",
        )

    is_admin = current_user.role == "admin"

    new_entity = RatedEntity(
        **entity.dict(),
        approval_status="approved" if is_admin else "under_review",
        approved_by=current_user.id if is_admin else None,
        approved_at=datetime.now(timezone.utc) if is_admin else None,
    )

    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


# ======================================================
# List Entities (PUBLIC)
# ✅ Only return approved entities
# ======================================================
@router.get("/entities", response_model=List[RatedEntityOut])
def list_entities(
    db: Session = Depends(get_db),

    # 🔍 SEARCH (NEW)
    search: str = Query(None),

    # existing filters
    type: str = Query(None),
    category: str = Query(None),
    jurisdiction: str = Query(None),

    # pagination
    limit: int = Query(20, le=50),
    cursor_score: float = Query(None),
    cursor_id: int = Query(None),
):
    # ======================================================
    # SEARCH MODE (bypasses cursor pagination)
    # ======================================================
    if search:
        q = f"%{search.lower()}%"

        return (
            db.query(RatedEntity)
            .filter(
                RatedEntity.approval_status == "approved",
                func.lower(
                    RatedEntity.name
                    + " "
                    + RatedEntity.state
                    + " "
                    + RatedEntity.county
                    + " "
                    + func.coalesce(RatedEntity.category, "")
                    + " "
                    + func.coalesce(RatedEntity.jurisdiction, "")
                ).like(q)
            )
            .order_by(
                RatedEntity.reputation_score.asc(),
                RatedEntity.id.asc()
            )
            .limit(100)
            .all()
        )


    query = db.query(RatedEntity).filter(
        RatedEntity.approval_status == "approved"
    )

    # filters
    if type:
        query = query.filter(RatedEntity.type == type)
    if category:
        query = query.filter(RatedEntity.category == category)
    if jurisdiction:
        query = query.filter(RatedEntity.jurisdiction == jurisdiction)

    # cursor pagination (LOW → HIGH)
    if cursor_score is not None and cursor_id is not None:
        query = query.filter(
            (
                (RatedEntity.reputation_score > cursor_score) |
                (
                    (RatedEntity.reputation_score == cursor_score) &
                    (RatedEntity.id > cursor_id)
                )
            )
        )

    # stable ordering
    query = query.order_by(
        RatedEntity.reputation_score.asc(),
        RatedEntity.id.asc()
    )

    return query.limit(limit).all()



# ======================================================
# Submit OR Update Rating (ONE per user per entity)
# ✅ Block rating if entity not approved
# ======================================================
@router.post("/submit", response_model=RatingCategoryScoreOut)
def submit_or_update_rating(
    rating: RatingCategoryScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 🔒 Must be an approved entity to receive ratings
    entity = db.query(RatedEntity).filter(
        RatedEntity.id == rating.entity_id,
        RatedEntity.approval_status == "approved",
    ).first()

    if not entity:
        raise HTTPException(
            status_code=400,
            detail="This entity is pending review and cannot be rated yet.",
        )

    existing = (
        db.query(RatingCategoryScore)
        .filter(
            RatingCategoryScore.user_id == current_user.id,
            RatingCategoryScore.entity_id == rating.entity_id,
        )
        .first()
    )

    # -----------------------------
    # UPDATE EXISTING RATING
    # -----------------------------
    if existing:
        existing.accountability = rating.accountability
        existing.respect = rating.respect
        existing.effectiveness = rating.effectiveness
        existing.transparency = rating.transparency
        existing.public_impact = rating.public_impact
        existing.comment = rating.comment
        existing.violated_rights = rating.violated_rights or []

        # Reset trust state on update
        existing.verified = False
        existing.flagged = False
        existing.flag_reason = None
        existing.flagged_by = None

        db.commit()

        # entity is already loaded above and approved
        entity.reputation_score = recalculate_reputation(entity.id, db)
        db.commit()

        return (
            db.query(RatingCategoryScore)
            .options(joinedload(RatingCategoryScore.user))
            .filter(RatingCategoryScore.id == existing.id)
            .first()
        )

    # -----------------------------
    # CREATE FIRST RATING
    # -----------------------------
    new_rating = RatingCategoryScore(
        user_id=current_user.id,
        entity_id=rating.entity_id,
        accountability=rating.accountability,
        respect=rating.respect,
        effectiveness=rating.effectiveness,
        transparency=rating.transparency,
        public_impact=rating.public_impact,
        comment=rating.comment,
        violated_rights=rating.violated_rights or [],
        verified=False,
    )

    db.add(new_rating)
    db.commit()

    # entity is already loaded above and approved
    entity.reputation_score = recalculate_reputation(entity.id, db)
    db.commit()

    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.id == new_rating.id)
        .first()
    )


# ======================================================
# Verify Rating (Admin)
# ======================================================
@router.post("/verify-rating/{rating_id}", response_model=RatingCategoryScoreOut)
def verify_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    rating = db.query(RatingCategoryScore).filter(
        RatingCategoryScore.id == rating_id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    rating.verified = True
    rating.flagged = False
    rating.flag_reason = None
    rating.flagged_by = None

    db.commit()

    entity = db.query(RatedEntity).filter(
        RatedEntity.id == rating.entity_id
    ).first()

    if entity:
        entity.reputation_score = recalculate_reputation(entity.id, db)
        db.commit()

    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.id == rating.id)
        .first()
    )


# ======================================================
# Delete Rating
# ======================================================
@router.delete("/delete-rating/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = db.query(RatingCategoryScore).filter(
        RatingCategoryScore.id == rating_id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    if rating.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    entity_id = rating.entity_id
    db.delete(rating)
    db.commit()

    entity = db.query(RatedEntity).filter(
        RatedEntity.id == entity_id
    ).first()

    if entity:
        entity.reputation_score = recalculate_reputation(entity.id, db)
        db.commit()

    return


# ======================================================
# Entity Reviews
# ======================================================
@router.get(
    "/entity/{entity_id}/reviews",
    response_model=List[RatingCategoryScoreOut],
)
def get_entity_reviews(entity_id: int, db: Session = Depends(get_db)):
    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.entity_id == entity_id)
        .order_by(RatingCategoryScore.created_at.desc())
        .all()
    )


# ======================================================
# Flag Rating
# ======================================================
@router.post("/flag-rating/{rating_id}")
def flag_rating(
    rating_id: int,
    flag: FlagRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = db.query(RatingCategoryScore).filter(
        RatingCategoryScore.id == rating_id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    rating.flagged = True
    rating.flag_reason = flag.reason
    rating.flagged_by = current_user.id
    db.commit()

    return {"message": "Rating flagged for admin review"}


# ======================================================
# Admin Views
# ======================================================
@router.get("/admin/flagged-ratings", response_model=List[RatingCategoryScoreOut])
def get_flagged_ratings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.flagged == True)
        .all()
    )


@router.get("/unverified", response_model=List[RatingCategoryScoreOut])
def get_unverified_ratings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.verified == False)
        .all()
    )


# ======================================================
# Get Current User's Rating for an Entity
# ======================================================
@router.get("/mine", response_model=RatingCategoryScoreOut)
def get_my_rating_for_entity(
    entity_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(
            RatingCategoryScore.user_id == current_user.id,
            RatingCategoryScore.entity_id == entity_id,
        )
        .first()
    )

    if not rating:
        raise HTTPException(
            status_code=404,
            detail="No rating found for this user and entity",
        )

    return rating
# ======================================================
# Get Single Approved Entity by ID (PUBLIC)
# ======================================================
@router.get("/entity/{entity_id}", response_model=RatedEntityOut)
def get_entity_by_id(
    entity_id: int,
    db: Session = Depends(get_db),
):
    entity = (
        db.query(RatedEntity)
        .filter(
            RatedEntity.id == entity_id,
            RatedEntity.approval_status == "approved",
        )
        .first()
    )

    if not entity:
        raise HTTPException(
            status_code=404,
            detail="Entity not found or not approved",
        )

    return entity
