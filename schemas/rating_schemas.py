from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ---------- RatedEntity ----------
class RatedEntityCreate(BaseModel):
    name: str
    type: str  # e.g. "individual", "agency", "institution"
    category: str  # e.g. "judge", "CPS", "hospital"
    jurisdiction: Optional[str] = None


class RatedEntityOut(RatedEntityCreate):
    id: int
    reputation_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- RatingCategoryScore ----------
class RatingCategoryScoreCreate(BaseModel):
    entity_id: int
    user_id: int
    accountability: int
    respect: int
    effectiveness: int
    transparency: int
    public_impact: int
    comment: Optional[str] = None


class RatingCategoryScoreOut(RatingCategoryScoreCreate):
    id: int
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- EvidenceAttachment ----------
class EvidenceAttachmentCreate(BaseModel):
    rating_id: int
    file_url: str
    description: Optional[str] = None


class EvidenceAttachmentOut(EvidenceAttachmentCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
