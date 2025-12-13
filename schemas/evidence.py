from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.user_public import PublicUserOut
from schemas.rating_schemas import RatedEntityOut


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

    # ✅ THESE MUST BE TOP-LEVEL FIELDS
    user: Optional[PublicUserOut]
    entity: Optional[RatedEntityOut]

    class Config:
        from_attributes = True
