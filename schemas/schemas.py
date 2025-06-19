from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = Field(default="official", pattern="^official$")  # ✅ restrict to 'official' only

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_anonymous: bool
    role: str

    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    email: EmailStr
    password: str
