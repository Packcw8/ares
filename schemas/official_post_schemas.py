from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OfficialPostCreate(BaseModel):
    title: str
    body: str
    entity_id: Optional[int]

class OfficialPostOut(BaseModel):
    id: int
    title: str
    body: str
    verified: bool
    created_at: datetime
    author_id: int
    entity_id: Optional[int]

    class Config:
        orm_mode = True
