from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from db import Base


class VaultEntry(Base):
    __tablename__ = "vault_entries"

    id = Column(Integer, primary_key=True, index=True)

    # 🔐 Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 🔗 Optional entity link
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=True)

    # 📝 Core documentation
    testimony = Column(Text, nullable=False)

    # 📍 Metadata
    incident_date = Column(DateTime(timezone=True), nullable=True)
    location = Column(String, nullable=True)
    category = Column(String, nullable=True)

    # 🔒 Privacy
    is_public = Column(Boolean, default=False, nullable=False)
    is_anonymous = Column(Boolean, default=False, nullable=False)

    # ⏱ Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    published_at = Column(DateTime(timezone=True), nullable=True)

    # 👤 Relationships (lazy by default = safer)
    user = relationship("User", lazy="joined")
    entity = relationship("RatedEntity", lazy="joined")
