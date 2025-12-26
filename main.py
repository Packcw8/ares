from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

# Database
from db import engine, Base

# Routers
from routes.auth_routes import router as auth_router
from routes.rating_routes import router as rating_router
from routes.official_post_routes import router as official_post_router
from routes.post_comment_routes import router as post_comment_router
from routes.admin_routes import router as admin_router
from routes import evidence
from routes import vault_entries
from routes import feed


# Import all models so SQLAlchemy registers tables
import models

# ======================================================
# FASTAPI APP (SINGLE INSTANCE)
# ======================================================
app = FastAPI(
    title="ARES API",
    version="0.1.0"
)

# ======================================================
# CORS (THIS IS ALL YOU NEED)
# ======================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.aresjustice.com",
        "https://aresjustice.com",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# STARTUP
# ======================================================
@app.on_event("startup")
def create_tables():
    print("🔧 Creating database tables (if missing)...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables ready!")

# ======================================================
# ROUTES
# ======================================================
app.include_router(auth_router)
app.include_router(rating_router)
app.include_router(official_post_router)
app.include_router(post_comment_router)
app.include_router(admin_router)
app.include_router(evidence.router)
app.include_router(vault_entries.router)
app.include_router(feed.router)


# Optional forum trailing-slash fix
@app.get("/forum", include_in_schema=False)
async def forum_redirect(request: Request):
    return RedirectResponse(url=str(request.url) + "/")

# ======================================================
# HEALTH CHECK (USE THIS TO VERIFY DEPLOY)
# ======================================================
@app.get("/__health")
def health():
    return {"status": "ok", "cors": "enabled"}

# ======================================================
# LOCAL DEV ENTRY
# ======================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, proxy_headers=True)
