from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base
from models.post_comment import PostComment
from sqlalchemy import ARRAY


class OfficialPost(Base):
    __tablename__ = "official_posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=True)  # Optional tie to agency/official

    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    from sqlalchemy import ARRAY

    # New fields
    is_pinned = Column(Boolean, default=False)
    is_ama = Column(Boolean, default=False)
    tags = Column(ARRAY(String), default=[])

    author = relationship("User")
    entity = relationship("RatedEntity")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete")
