from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from db import Base

class OfficialPost(Base):
    __tablename__ = "official_posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=True)  # Optional tie to agency/official

    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    verified = Column(Boolean, default=True)

    # Store in UTC, timezone-aware
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # New fields
    is_pinned = Column(Boolean, default=False)
    is_ama = Column(Boolean, default=False)

    # IMPORTANT: use default=list, not default=[]
    tags = Column(ARRAY(String), default=list)

    author = relationship("User")
    entity = relationship("RatedEntity")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete")
