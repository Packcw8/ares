from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Core identity
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Roles
    role = Column(String, default="citizen")  # citizen | official_pending | official_verified | admin

    # Email verification
    is_email_verified = Column(Boolean, default=False)
    email_verification_token_hash = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    # Official verification (admin-controlled)
    is_verified = Column(Boolean, default=False)
    official_verified_at = Column(DateTime, nullable=True)
    verified_by_admin_id = Column(Integer, nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Official metadata (ALL NULLABLE — SAFE)
    full_name = Column(String, nullable=True)
    title = Column(String, nullable=True)
    agency = Column(String, nullable=True)
    official_email = Column(String, nullable=True)
    state = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)

    is_anonymous = Column(Boolean, default=False)
