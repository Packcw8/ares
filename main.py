from fastapi import FastAPI
from db import engine, Base
from auth_routes import router as auth_router
from rating_routes import router as rating_router
import os

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Include your routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(rating_router, prefix="/ratings", tags=["ratings"])

# Health check route
@app.get("/health")
def health_check():
    return {"status": "ok"}

# TEMP: Debug environment variable from Azure
@app.get("/debug-db")
def debug_db():
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }

# Only used for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
