from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db import Base


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)

    # 📦 Storage
    blob_url = Column(String, nullable=False)

    # 📝 Metadata
    description = Column(String)
    tags = Column(String)
    location = Column(String)

    # 🔒 Visibility (temporary – later inherited from vault entry)
    is_public = Column(Boolean, default=False)
    is_anonymous = Column(Boolean, default=False)

    # ⏱ Timestamp (UTC)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # 🔗 Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Entity is OPTIONAL now (important)
    entity_id = Column(Integer, ForeignKey("rated_entities.id"), nullable=True)

    # 🔗 NEW: Link to Vault Entry
    vault_entry_id = Column(
        Integer,
        ForeignKey("vault_entries.id"),
        nullable=True,
    )

    # 👤 Relationships
    user = relationship("User")
    entity = relationship("RatedEntity")
    vault_entry = relationship("VaultEntry")
