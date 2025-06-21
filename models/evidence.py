from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # 🔗 Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=False)

    # 👤 Relationships
    user = relationship("User")
    entity = relationship("RatedEntity")
