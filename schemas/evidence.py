from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from schemas.user_public import PublicUserOut


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
#=============================================================
#public User
#=============================================================
    class Config:
        # ✅ Pydantic v2 replacement for orm_mode

        from_attributes = True

        user: Optional[PublicUserOut]

        model_config = {"from_attributes": True}
