from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    blob_url = Column(String, nullable=False)
    description = Column(String)
    tags = Column(String)
    location = Column(String)
    is_public = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=False)

    # Store in UTC, timezone-aware
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # 🔗 Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=False)

    # 👤 Relationships
    user = relationship("User")
    entity = relationship("RatedEntity")
