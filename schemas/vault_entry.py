from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VaultEntryCreate(BaseModel):
    testimony: str
    entity_id: Optional[int] = None
    incident_date: Optional[datetime] = None
    location: Optional[str] = None
    category: Optional[str] = None
    is_anonymous: bool = False
    is_public: bool = False
