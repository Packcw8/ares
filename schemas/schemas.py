from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = Field(default="citizen")

    @validator("role")
    def validate_role(cls, v):
        allowed_roles = {"citizen", "official"}
        if v not in allowed_roles:
            raise ValueError("Only 'citizen' or 'official' roles are allowed at signup")
        return v


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_anonymous: bool
    is_verified: bool

    model_config = {
        "from_attributes": True
    }


class UserLogin(BaseModel):
    email: EmailStr
    password: str
