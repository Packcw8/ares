from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from models.rating import Official, Complaint, Feedback
from models.user import User
from schemas.official_schemas import (
    OfficialCreate, OfficialOut,
    ComplaintCreate, ComplaintOut,
    FeedbackCreate, FeedbackOut
)
from utils.auth import get_current_user

router = APIRouter(prefix="/officials", tags=["officials"])


# ---------- CREATE NEW OFFICIAL ----------
@router.post("/", response_model=OfficialOut)
def create_official(official: OfficialCreate, db: Session = Depends(get_db)):
    new_official = Official(**official.dict())
    db.add(new_official)
    db.commit()
    db.refresh(new_official)
    return new_official


# ---------- GET ALL OFFICIALS ----------
@router.get("/", response_model=list[OfficialOut])
def list_officials(db: Session = Depends(get_db)):
    return db.query(Official).order_by(Official.reputation_score.asc()).all()


# ---------- SUBMIT COMPLAINT ----------
@router.post("/complaints", response_model=ComplaintOut)
def submit_complaint(
    complaint: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save complaint unverified
    new_complaint = Complaint(
        user_id=current_user.id,
        official_id=complaint.official_id,
        description=complaint.description,
        severity=complaint.severity,
        verified=False,
    )
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    return new_complaint


# ---------- SUBMIT POSITIVE FEEDBACK ----------
@router.post("/feedbacks", response_model=FeedbackOut)
def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_feedback = Feedback(
        user_id=current_user.id,
        official_id=feedback.official_id,
        comment=feedback.comment,
        impact=feedback.impact
    )

    # Apply positive impact
    official = db.query(Official).filter(Official.id == feedback.official_id).first()
    if not official:
        raise HTTPException(status_code=404, detail="Official not found")

    official.reputation_score = min(100.0, official.reputation_score + feedback.impact)
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    return new_feedback


# ---------- VERIFY A COMPLAINT (ADMIN-ONLY LATER) ----------
@router.post("/verify-complaint/{complaint_id}", response_model=ComplaintOut)
def verify_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Add is_admin check later
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.verified:
        raise HTTPException(status_code=400, detail="Complaint already verified")

    complaint.verified = True
    deduction = complaint.severity * 2.5

    official = db.query(Official).filter(Official.id == complaint.official_id).first()
    if official:
        official.reputation_score = max(0.0, official.reputation_score - deduction)

    db.commit()
    db.refresh(complaint)
    return complaint
