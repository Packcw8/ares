from fastapi import FastAPI
from db import engine, Base
from routes.auth_routes import router as auth_router
import uvicorn
from routes.rating_routes import router as rating_router
from fastapi.middleware.cors import CORSMiddleware  # <-- CORS import

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:3000",  # Local dev
    "https://zealous-field-079ebd30f.6.azurestaticapps.net",  # Deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_router)
app.include_router(rating_router)

# Health check route
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Entry point for local dev
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
