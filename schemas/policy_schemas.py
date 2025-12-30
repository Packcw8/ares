from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ----------------------------
# POLICY
# ----------------------------

class PolicyCreate(BaseModel):
    title: str
    summary: Optional[str] = None
    jurisdiction_level: str = Field(..., pattern="^(federal|state)$")
    state_code: Optional[str] = Field(None, min_length=2, max_length=2)
    governing_body: Optional[str] = None
    introduced_date: Optional[date] = None


class PolicyOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    jurisdiction_level: str
    state_code: Optional[str]
    governing_body: Optional[str]
    current_status_id: Optional[int]
    introduced_date: Optional[date]
    is_active: bool

    # ✅ THIS IS THE FIX
    rated_entity_id: Optional[int] = None

    created_at: datetime

    model_config = {"from_attributes": True}


# ----------------------------
# STATUS
# ----------------------------

class PolicyStatusOut(BaseModel):
    id: int
    code: str
    label: str

    model_config = {"from_attributes": True}


# ----------------------------
# STATUS CHANGE REQUEST
# ----------------------------

class PolicyStatusChangeRequestCreate(BaseModel):
    policy_id: int
    requested_status_id: int
    source_link: Optional[str] = None
    note: Optional[str] = None


class PolicyStatusChangeRequestOut(BaseModel):
    id: int
    policy_id: int
    requested_status_id: int
    approval_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
