from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = Field(default="citizen")

    # Official-only fields
    full_name: Optional[str] = None
    title: Optional[str] = None
    agency: Optional[str] = None
    official_email: Optional[EmailStr] = None
    state: Optional[str] = None
    jurisdiction: Optional[str] = None

    @validator("role")
    def validate_role(cls, v):
        if v not in {"citizen", "official"}:
            raise ValueError("Only 'citizen' or 'official' roles are allowed at signup")
        return v

    @validator("full_name", "title", "agency", "official_email", "state", "jurisdiction", always=True)
    def validate_official_fields(cls, v, values, field):
        if values.get("role") == "official" and not v:
            raise ValueError(f"{field.name.replace('_', ' ').title()} is required for officials")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_verified: bool
    is_anonymous: bool

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    identifier: str
    password: str
