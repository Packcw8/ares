import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ✅ Read full PostgreSQL connection string from environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# ✅ Create SQLAlchemy engine with this URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# ✅ Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Declare the base class for models
Base = declarative_base()

# ✅ Dependency to get a database session in FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
