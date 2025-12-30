from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from db import Base


# ======================================================
# Rated Entity
# ======================================================
class RatedEntity(Base):
    __tablename__ = "rated_entities"

    __table_args__ = (
        Index("idx_reputation_cursor", "reputation_score", "id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String, nullable=True)
    jurisdiction = Column(String)
    state = Column(String, nullable=False, index=True)
    county = Column(String, nullable=False, index=True)

    reputation_score = Column(Float, default=100.0)

    approval_status = Column(String, nullable=False, default="under_review")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    ratings = relationship(
        "RatingCategoryScore",
        back_populates="entity",
        cascade="all, delete-orphan"
    )

    evidence = relationship(
        "EvidenceAttachment",
        back_populates="entity",
        cascade="all, delete-orphan"
    )

# ======================================================
# Category-Based Rating Score
# ======================================================
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

    comment = Column(String(2000))
    verified = Column(Boolean, default=False)
    violated_rights = Column(ARRAY(String), nullable=True, default=list)

    flagged = Column(Boolean, default=False)
    flag_reason = Column(String(1000), nullable=True)
    flagged_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    entity = relationship("RatedEntity", back_populates="ratings")


# ======================================================
# Evidence Attachments (linked to RatedEntity)
# ======================================================
class EvidenceAttachment(Base):
    __tablename__ = "evidence_attachments"

    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=False)
    score_id = Column(Integer, ForeignKey("rating_scores.id"), nullable=True)

    file_url = Column(String)
    case_number = Column(String)
    location = Column(String)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    entity = relationship("RatedEntity", back_populates="evidence")
