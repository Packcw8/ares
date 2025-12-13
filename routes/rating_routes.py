from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List

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


# ---------- Recalculate reputation ----------
def recalculate_reputation(entity_id: int, db: Session) -> float:
    scores = (
        db.query(RatingCategoryScore)
        .filter(RatingCategoryScore.entity_id == entity_id)
        .all()
    )

    if not scores:
        return 100.0

    total = 0
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


# ---------- Create Rated Entity ----------
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

    new_entity = RatedEntity(**entity.dict())
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


# ---------- Get Entities ----------
@router.get("/entities", response_model=List[RatedEntityOut])
def list_entities(
    db: Session = Depends(get_db),
    type: str = Query(None),
    category: str = Query(None),
    jurisdiction: str = Query(None),
    sort_by: str = Query("reputation_score"),
):
    query = db.query(RatedEntity)

    if type:
        query = query.filter(RatedEntity.type == type)
    if category:
        query = query.filter(RatedEntity.category == category)
    if jurisdiction:
        query = query.filter(RatedEntity.jurisdiction == jurisdiction)

    if sort_by == "created_at":
        query = query.order_by(RatedEntity.created_at.desc())
    else:
        query = query.order_by(RatedEntity.reputation_score.asc())

    return query.all()


# ---------- Submit Rating ----------
@router.post("/submit", response_model=RatingCategoryScoreOut)
def submit_rating(
    rating: RatingCategoryScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    entity = db.query(RatedEntity).filter(
        RatedEntity.id == rating.entity_id
    ).first()

    if entity:
        avg = (
            rating.accountability
            + rating.respect
            + rating.effectiveness
            + rating.transparency
            + rating.public_impact
        ) / 5
        entity.reputation_score = max(
            0.0, entity.reputation_score + (avg - 5) * 1.5
        )

    db.commit()
    db.refresh(new_rating)

    # 🔑 reload with user
    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.id == new_rating.id)
        .first()
    )


# ---------- Verify Rating ----------
@router.post("/verify-rating/{rating_id}", response_model=RatingCategoryScoreOut)
def verify_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = db.query(RatingCategoryScore).filter(
        RatingCategoryScore.id == rating_id
    ).first()

    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    rating.verified = True
    rating.flagged = False
    rating.flag_reason = None
    rating.flagged_by = None

    entity = db.query(RatedEntity).filter(
        RatedEntity.id == rating.entity_id
    ).first()

    if entity:
        avg = (
            rating.accountability
            + rating.respect
            + rating.effectiveness
            + rating.transparency
            + rating.public_impact
        ) / 5
        entity.reputation_score = max(
            0.0, entity.reputation_score + (avg - 5) * 2.5
        )

    db.commit()

    return (
        db.query(RatingCategoryScore)
        .options(joinedload(RatingCategoryScore.user))
        .filter(RatingCategoryScore.id == rating.id)
        .first()
    )


# ---------- Delete Rating ----------
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

    if rating.user_id != current_user.id:
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


# ---------- Entity Reviews ----------
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


# ---------- Flag Rating ----------
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


# ---------- Admin Views ----------
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
