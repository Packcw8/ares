from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.sql import func
from db import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    blob_url = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    location = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
