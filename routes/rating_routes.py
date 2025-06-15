from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from db import get_db
from models.rating import RatedEntity, RatingCategoryScore, EvidenceAttachment

from models.user import User
from utils.auth import get_current_user
from schemas.rating_schemas import (
    RatedEntityCreate, RatedEntityOut,
    RatingCategoryScoreCreate, RatingCategoryScoreOut,
    EvidenceAttachmentCreate, EvidenceAttachmentOut
)


router = APIRouter(prefix="/ratings", tags=["ratings"])


# ---------- Create a Rated Entity ----------
@router.post("/entities", response_model=RatedEntityOut)
def create_entity(entity: RatedEntityCreate, db: Session = Depends(get_db)):
    new_entity = RatedEntity(**entity.dict())
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


# ---------- Get All Rated Entities ----------
@router.get("/entities", response_model=list[RatedEntityOut])
def list_entities(
    db: Session = Depends(get_db),
    type: str = Query(None, description="Filter by entity type"),
    category: str = Query(None, description="Filter by category"),
    jurisdiction: str = Query(None, description="Filter by jurisdiction"),
    sort_by: str = Query("reputation_score", description="Sort by reputation_score or created_at")
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


# ---------- Submit a Category-Based Rating ----------
@router.post("/submit", response_model=RatingCategoryScoreOut)
def submit_rating(
    rating: RatingCategoryScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        verified=False,
    )

    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating


# ---------- Submit Evidence for a Rating ----------
@router.post("/evidence", response_model=EvidenceAttachmentOut)
def submit_evidence(
    evidence: EvidenceAttachmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_evidence = EvidenceAttachment(**evidence.dict())
    db.add(new_evidence)
    db.commit()
    db.refresh(new_evidence)
    return new_evidence


# ---------- Admin Verifies a Rating ----------
@router.post("/verify-rating/{rating_id}", response_model=RatingCategoryScoreOut)
def verify_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Optional: add admin check
):
    rating = db.query(RatingCategoryScore).filter(RatingCategoryScore.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if rating.verified:
        raise HTTPException(status_code=400, detail="Rating already verified")

    rating.verified = True

    # Adjust reputation
    avg_score = sum([
        rating.accountability,
        rating.respect,
        rating.effectiveness,
        rating.transparency,
        rating.public_impact
    ]) / 5

    deduction = (10 - avg_score) * 2  # Lower scores = bigger penalty
    entity = db.query(RatedEntity).filter(RatedEntity.id == rating.entity_id).first()
    if entity:
        entity.reputation_score = max(0.0, entity.reputation_score - deduction)

    db.commit()
    db.refresh(rating)
    return rating
