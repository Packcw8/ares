from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from db import engine, Base
from routes.auth_routes import router as auth_router
from routes.rating_routes import router as rating_router
from routes.official_post_routes import router as official_post_router
from routes.post_comment_routes import router as post_comment_router
from routes.admin_routes import router as admin_router
from routes import evidence

from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:3000",  # Local dev
    "https://ashy-tree-0ea272d0f.6.azurestaticapps.net",
    "https://www.aresjustice.com",
    "https://aresjustice.com",
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
app.include_router(evidence.router)

@app.get("/forum", include_in_schema=False)
async def forum_redirect(request: Request):
    return RedirectResponse(url=str(request.url) + "/")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/debug-db")
def debug_db():
    return {
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }

# Manual OPTIONS handler to ensure Azure handles CORS preflight requests
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Origin": origin if origin in origins else "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS, DELETE, PATCH",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    }
    return JSONResponse(content={"message": "CORS preflight OK"}, headers=headers)

# Entry point for local development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, proxy_headers=True)
