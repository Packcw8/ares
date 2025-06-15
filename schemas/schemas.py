from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  # plain-text password input

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_anonymous: bool

    model_config = {
        "from_attributes": True
    }

class UserLogin(BaseModel):
    email: EmailStr
    password: str
