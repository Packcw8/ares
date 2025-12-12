from sqlalchemy import Column, Integer, String, Boolean, DateTime
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # 🔐 Email verification
    is_email_verified = Column(Boolean, default=False)
    email_verification_token_hash = Column(String, nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)

    # ✅ Official verification (admin-controlled)
    is_verified = Column(Boolean, default=False)

    is_anonymous = Column(Boolean, default=False)
    role = Column(String, default="citizen")
