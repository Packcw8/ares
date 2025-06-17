from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func  # ✅ Added for case-insensitive duplicate check
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


# ---------- Recalculate reputation based on all remaining ratings ----------
def recalculate_reputation(entity_id: int, db: Session) -> float:
    scores = db.query(RatingCategoryScore).filter(
        RatingCategoryScore.entity_id == entity_id
    ).all()

    if not scores:
        return 100.0

    total = 0
    for s in scores:
        avg = sum([
            s.accountability,
            s.respect,
            s.effectiveness,
            s.transparency,
            s.public_impact
        ]) / 5
        weight = 2.5 if s.verified else 1.5
        total += (avg - 5) * weight

    return max(0.0, 100.0 + total)


# ---------- Create a Rated Entity ----------
@router.post("/entities", response_model=RatedEntityOut)
def create_entity(entity: RatedEntityCreate, db: Session = Depends(get_db)):
    # ✅ Case-insensitive duplicate check
    existing = db.query(RatedEntity).filter(
        func.lower(RatedEntity.name) == entity.name.strip().lower(),
        RatedEntity.type == entity.type,
        RatedEntity.state == entity.state,
        RatedEntity.county == entity.county
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="An entity with the same name, type, state, and county already exists."
        )

    new_entity = RatedEntity(**entity.dict())
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


# ---------- Get All Rated Entities ----------
@router.get("/entities", response_model=list[RatedEntityOut])
def list_entities(
    db: Session = Depends(get_db),
    type: str = Query(None),
    category: str = Query(None),
    jurisdiction: str = Query(None),
    sort_by: str = Query("reputation_score")
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

    # Light immediate impact
    avg_score = sum([
        new_rating.accountability,
        new_rating.respect,
        new_rating.effectiveness,
        new_rating.transparency,
        new_rating.public_impact
    ]) / 5

    impact = (avg_score - 5) * 1.5

    entity = db.query(RatedEntity).filter(RatedEntity.id == rating.entity_id).first()
    if entity:
        entity.reputation_score = max(0.0, entity.reputation_score + impact)

    db.commit()
    db.refresh(new_rating)
    return new_rating


# ---------- Verify a Rating ----------
@router.post("/verify-rating/{rating_id}", response_model=RatingCategoryScoreOut)
def verify_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(RatingCategoryScore).filter(RatingCategoryScore.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if rating.verified:
        raise HTTPException(status_code=400, detail="Rating already verified")

    rating.verified = True

    avg_score = sum([
        rating.accountability,
        rating.respect,
        rating.effectiveness,
        rating.transparency,
        rating.public_impact
    ]) / 5

    impact = (avg_score - 5) * 2.5

    entity = db.query(RatedEntity).filter(RatedEntity.id == rating.entity_id).first()
    if entity:
        entity.reputation_score = max(0.0, entity.reputation_score + impact)

    db.commit()
    db.refresh(rating)
    return rating


# ---------- Delete Rating (False Complaint) ----------
@router.delete("/delete-rating/{rating_id}")
def delete_rating(
    rating_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rating = db.query(RatingCategoryScore).filter(RatingCategoryScore.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    entity = db.query(RatedEntity).filter(RatedEntity.id == rating.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Associated entity not found")

    db.delete(rating)
    db.commit()

    # Recalculate entity's reputation from scratch
    entity.reputation_score = recalculate_reputation(entity.id, db)
    db.commit()

    return {"message": "Rating deleted and reputation recalculated", "new_score": entity.reputation_score}


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
# ---------- Get All Reviews for One Entity ----------
@router.get("/entity/{entity_id}/reviews", response_model=list[RatingCategoryScoreOut])
def get_entity_reviews(entity_id: int, db: Session = Depends(get_db)):
    reviews = db.query(RatingCategoryScore).filter(RatingCategoryScore.entity_id == entity_id).all()
    return reviews
