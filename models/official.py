from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from db import Base

class Official(Base):
    __tablename__ = "officials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    position = Column(String)
    agency = Column(String)
    jurisdiction = Column(String)
    reputation_score = Column(Float, default=100.0)
    created_at = Column(DateTime, server_default=func.now())

    complaints = relationship("Complaint", back_populates="official")
    feedbacks = relationship("Feedback", back_populates="official")


class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    official_id = Column(Integer, ForeignKey("officials.id"))
    description = Column(String)
    severity = Column(Integer)  # 1–10
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    official = relationship("Official", back_populates="complaints")


class Feedback(Base):
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    official_id = Column(Integer, ForeignKey("officials.id"))
    comment = Column(String)
    impact = Column(Integer, default=1)  # +1 to +5
    created_at = Column(DateTime, server_default=func.now())

    official = relationship("Official", back_populates="feedbacks")
