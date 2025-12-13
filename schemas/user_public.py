from pydantic import BaseModel
from typing import Optional

class PublicUserOut(BaseModel):
    username: Optional[str] = None
    is_anonymous: bool = False

    @property
    def display_name(self) -> str:
        if self.is_anonymous or not self.username:
            return "Anonymous"
        return self.username

    model_config = {"from_attributes": True}
