from pydantic import BaseModel
from datetime import datetime

class PostCommentCreate(BaseModel):
    post_id: int
    content: str

class PostCommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        orm_mode = True
