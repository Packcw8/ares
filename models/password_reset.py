from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    # Store a HASH of the token (never store raw token in DB)
    token_hash = Column(String, unique=True, index=True, nullable=False)

    expires_at = Column(DateTime(timezone=True), index=True, nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")

# Helpful index for cleanup queries (expired tokens)
Index("ix_password_reset_tokens_expires_used", PasswordResetToken.expires_at, PasswordResetToken.used)
