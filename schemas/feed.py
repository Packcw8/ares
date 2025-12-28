from pydantic import BaseModel
from typing import Optional, Union, Literal
from datetime import datetime

from schemas.user_public import PublicUserOut
from schemas.rating_schemas import (
    RatedEntityOut,
    RatingCategoryScoreOut,
)

# ======================================================
# Base Feed Item
# ======================================================
class FeedItemBase(BaseModel):
    type: str
    created_at: datetime


# ======================================================
# Vault Record Feed Item
# ======================================================
class VaultRecordFeedItem(FeedItemBase):
    type: Literal["vault_record"]
    entity: Optional[RatedEntityOut] = None
    description: str
    media: list[dict] = []
    user: Optional[PublicUserOut] = None



# ======================================================
# Entity Created Feed Item
# ======================================================
class EntityCreatedFeedItem(FeedItemBase):
    type: Literal["entity_created"]
    entity: RatedEntityOut
    user: Optional[PublicUserOut] = None


# ======================================================
# Rating Feed Item
# ======================================================
class RatingFeedItem(FeedItemBase):
    type: Literal["rating"]
    entity: RatedEntityOut
    rating: RatingCategoryScoreOut
    user: PublicUserOut


# ======================================================
# Forum / Official Post Feed Item
# ======================================================
class ForumPostFeedItem(FeedItemBase):
    type: Literal["forum_post"]
    entity: Optional[RatedEntityOut] = None
    title: str
    body: str
    user: PublicUserOut
    is_pinned: bool = False
    is_ama: bool = False


# ======================================================
# Unified Feed Output (Discriminated Union)
# ======================================================
FeedItemOut = Union[
    VaultRecordFeedItem,
    EntityCreatedFeedItem,
    RatingFeedItem,
    ForumPostFeedItem,
]
