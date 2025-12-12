from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ======================================================
# Evidence creation (metadata only)
# ======================================================

class EvidenceCreate(BaseModel):
    blob_url: str
    description: Optional[str] = None
    tags: Optional[str] = None
    location: Optional[str] = None
    is_public: bool = True
    is_anonymous: bool = False
    entity_id: int


# ======================================================
# Evidence output (DB → API)
# ======================================================

class EvidenceOut(EvidenceCreate):
    id: int
    timestamp: datetime

    class Config:
        # ✅ Pydantic v2 replacement for orm_mode
        from_attributes = True
