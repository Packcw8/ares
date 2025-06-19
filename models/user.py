from sqlalchemy import Column, Integer, String, Boolean
from db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # 👈 updated from 'name' to 'username'
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)        # ✅ used to verify officials
    is_anonymous = Column(Boolean, default=False)
    role = Column(String, default="official")           # ✅ only 'official' allowed on signup
