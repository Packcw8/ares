from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db import Base

class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("official_posts.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    content = Column(Text, nullable=False)

    # Store in UTC, timezone-aware
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    post = relationship("OfficialPost", back_populates="comments")
    user = relationship("User")
