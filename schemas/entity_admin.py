from pydantic import BaseModel
from typing import Optional

class AdminEntityUpdate(BaseModel):
    name: Optional[str]
    category: Optional[str]
    jurisdiction: Optional[str]
    state: Optional[str]
    county: Optional[str]
