from pydantic import BaseModel
from datetime import datetime
from schemas.user_public import PublicUserOut

class PostCommentCreate(BaseModel):
    post_id: int
    content: str


class PostCommentOut(BaseModel):
    id: int
    post_id: int
    content: str
    created_at: datetime

    # 👤 NEW
    user: PublicUserOut

    model_config = {"from_attributes": True}
