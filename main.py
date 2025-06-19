from fastapi import FastAPI
from db import engine, Base
from routes.auth_routes import router as auth_router
from routes.rating_routes import router as rating_router
from routes.official_post_routes import router as official_post_router
from routes.post_comment_routes import router as post_comment_router
from routes.admin_routes import router as admin_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

import os
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# Custom proxy trust middleware for Azure
class CustomProxyHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("x-forwarded-proto") == "https":
            request.scope["scheme"] = "https"
        return await call_next(request)

# Add middleware
app.add_middleware(CustomProxyHeaderMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

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
app.include_router(official_post_router)
app.include_router(post_comment_router)
app.include_router(admin_router)

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, proxy_headers=True)
