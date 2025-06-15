from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ---------- Officials ----------
class OfficialCreate(BaseModel):
    name: str
    position: str
    agency: Optional[str]
    jurisdiction: Optional[str]

class OfficialOut(OfficialCreate):
    id: int
    reputation_score: float
    created_at: datetime

    class Config:
        orm_mode = True

# ---------- Complaints ----------
class ComplaintCreate(BaseModel):
    official_id: int
    description: str
    severity: int  # 1–10

class ComplaintOut(BaseModel):
    id: int
    official_id: int
    user_id: int
    description: str
    severity: int
    verified: bool
    created_at: datetime

    class Config:
        orm_mode = True

# ---------- Feedback ----------
class FeedbackCreate(BaseModel):
    official_id: int
    comment: Optional[str]
    impact: int  # +1 to +5

class FeedbackOut(BaseModel):
    id: int
    official_id: int
    user_id: int
    comment: Optional[str]
    impact: int
    created_at: datetime

    class Config:
        orm_mode = True
