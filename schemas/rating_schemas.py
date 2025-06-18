from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# ---------- RatedEntity ----------
class RatedEntityCreate(BaseModel):
    name: str
    type: str  # e.g. "individual", "agency", "institution"
    category: str  # e.g. "judge", "CPS", "hospital"
    jurisdiction: Optional[str] = None
    state: str
    county: str


class RatedEntityOut(RatedEntityCreate):
    id: int
    reputation_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- RatingCategoryScore ----------
class RatingCategoryScoreCreate(BaseModel):
    entity_id: int
    accountability: int
    respect: int
    effectiveness: int
    transparency: int
    public_impact: int
    comment: Optional[str] = None
    violated_rights: Optional[List[str]] = []  # ✅ Added field for tagging constitutional violations


class RatingCategoryScoreOut(RatingCategoryScoreCreate):
    id: int
    verified: bool
    created_at: datetime
    user_id: int  # include for output, not input

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
