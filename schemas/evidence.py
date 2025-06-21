from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EvidenceCreate(BaseModel):
    blob_url: str
    description: Optional[str]
    tags: Optional[str]
    location: Optional[str]
    is_public: bool
    is_anonymous: bool
    entity_id: int  # required
    user_id: Optional[int] = None  # optional, backend usually fills this

class EvidenceOut(EvidenceCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
