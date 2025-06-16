from fastapi import FastAPI
from db import engine, Base
from routes.auth_routes import router as auth_router
from routes.rating_routes import router as rating_router
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:3000",  # Local dev
    "https://ashy-tree-0ea272d0f.6.azurestaticapps.net",  # Deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(rating_router)

# Health check route
@app.get("/health")
def health_check():
    return {"status": "ok"}

# TEMP: Debug Azure's environment variable
@app.get("/debug-db")
def debug_db():
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }

# Entry point for local development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
