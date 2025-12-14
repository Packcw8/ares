from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from schemas.user_public import PublicUserOut


# ======================================================
# Rated Entity (Create)
# ======================================================
class RatedEntityCreate(BaseModel):
    name: str
    type: str  # e.g. "individual", "agency", "institution"
    category: str  # e.g. "judge", "CPS", "hospital"
    jurisdiction: Optional[str] = None
    state: str
    county: str


# ======================================================
# Rated Entity (Output)
# ======================================================
class RatedEntityOut(RatedEntityCreate):
    id: int
    reputation_score: float

    # 🔒 Moderation fields
    approval_status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None

    created_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# RatingCategoryScore (Create)
# ======================================================
class RatingCategoryScoreCreate(BaseModel):
    entity_id: int
    accountability: int
    respect: int
    effectiveness: int
    transparency: int
    public_impact: int
    comment: Optional[str] = None
    violated_rights: Optional[List[str]] = []


# ======================================================
# RatingCategoryScore (Output)
# ======================================================
class RatingCategoryScoreOut(RatingCategoryScoreCreate):
    id: int
    verified: bool
    created_at: datetime

    # 👤 User info
    user: PublicUserOut

    # 🚩 Moderation
    flagged: Optional[bool] = False
    flag_reason: Optional[str] = None
    flagged_by: Optional[int] = None

    # 🔗 Entity (approved only is enforced in routes)
    entity: Optional[RatedEntityOut] = None

    class Config:
        from_attributes = True


# ======================================================
# EvidenceAttachment (Create)
# ======================================================
class EvidenceAttachmentCreate(BaseModel):
    rating_id: int
    file_url: str
    description: Optional[str] = None


# ======================================================
# EvidenceAttachment (Output)
# ======================================================
class EvidenceAttachmentOut(EvidenceAttachmentCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ======================================================
# Flag Request
# ======================================================
class FlagRequest(BaseModel):
    reason: str
