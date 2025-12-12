from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = Field(default="citizen")

    # Official-only fields (nullable in DB, validated here)
    full_name: Optional[str] = None
    title: Optional[str] = None
    agency: Optional[str] = None
    official_email: Optional[EmailStr] = None
    state: Optional[str] = None
    jurisdiction: Optional[str] = None

    @model_validator(mode="after")
    def validate_official_fields(self):
        if self.role == "official":
            missing = []

            if not self.full_name:
                missing.append("full_name")
            if not self.title:
                missing.append("title")
            if not self.agency:
                missing.append("agency")
            if not self.official_email:
                missing.append("official_email")
            if not self.state:
                missing.append("state")
            if not self.jurisdiction:
                missing.append("jurisdiction")

            if missing:
                raise ValueError(
                    f"Missing required official fields: {', '.join(missing)}"
                )

        if self.role not in {"citizen", "official"}:
            raise ValueError("Invalid role")

        return self


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
