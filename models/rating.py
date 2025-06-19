from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from db import Base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Column, String

# ---------- Rated Entity ----------
class RatedEntity(Base):
    __tablename__ = "rated_entities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'official', 'agency', 'institution'
    category = Column(String, nullable=True)  # e.g., 'judge', 'CPS', 'jail'
    jurisdiction = Column(String)
    state = Column(String, nullable=False, index=True)     # <-- NEW
    county = Column(String, nullable=False, index=True)    # <-- NEW
    reputation_score = Column(Float, default=100.0)
    created_at = Column(DateTime, server_default=func.now())

    ratings = relationship("RatingCategoryScore", back_populates="entity", cascade="all, delete-orphan")
    evidence = relationship("EvidenceAttachment", back_populates="entity", cascade="all, delete-orphan")



# ---------- Category-Based Score ----------
class RatingCategoryScore(Base):
    __tablename__ = "rating_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=False)

    accountability = Column(Integer)
    respect = Column(Integer)
    effectiveness = Column(Integer)
    transparency = Column(Integer)
    public_impact = Column(Integer)

    comment = Column(String(2000))  # or longer if needed
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    entity = relationship("RatedEntity", back_populates="ratings")
    violated_rights = Column(ARRAY(String), nullable=True, default=[])
    flagged = Column(Boolean, default=False)
    flag_reason = Column(String(1000), nullable=True)
    flagged_by = Column(Integer, ForeignKey("users.id"), nullable=True)


# ---------- Evidence Attachments ----------
class EvidenceAttachment(Base):
    __tablename__ = "evidence_attachments"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=False)
    score_id = Column(Integer, ForeignKey("rating_scores.id"), nullable=True)

    file_url = Column(String)
    case_number = Column(String)
    location = Column(String)
    created_at = Column(DateTime, server_default=func.now())

    entity = relationship("RatedEntity", back_populates="evidence")
