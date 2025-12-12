from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from schemas.schemas import UserCreate, UserOut, UserLogin
from models.user import User
from db import get_db
from utils.auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
)

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth", tags=["auth"])

# ======================================================
# Email verification helpers
# ======================================================

VERIFY_TTL_HOURS = 24

def make_verify_token():
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=VERIFY_TTL_HOURS)
    return token, token_hash, expires_at

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

# ======================================================
# CORS preflight
# ======================================================

@router.options("/signup")
async def signup_options(request: Request):
    origin = request.headers.get("origin")
    headers = {
        "Access-Control-Allow-Origin": origin if origin in [
            "https://www.aresjustice.com",
            "https://aresjustice.com",
            "http://localhost:3000"
        ] else "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    }
    return JSONResponse(content={"message": "Signup CORS preflight OK"}, headers=headers)

# ======================================================
# Signup
# ======================================================

@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # keep existing official verification behavior
    is_verified = False if user.role == "official" else True

    # generate email verification token (hash stored)
    _, token_hash, expires_at = make_verify_token()

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        is_verified=is_verified,

        is_email_verified=False,
        email_verification_token_hash=token_hash,
        email_verification_expires_at=expires_at,
        email_verified_at=None,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ======================================================
# Login
# ======================================================

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={
        "sub": str(db_user.id),
        "role": db_user.role
    })

    return {"access_token": access_token, "token_type": "bearer"}

# ======================================================
# Current user
# ======================================================

@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# ======================================================
# Verify email
# ======================================================

class VerifyEmailPayload(BaseModel):
    email: EmailStr
    token: str

@router.post("/verify-email")
def verify_email(payload: VerifyEmailPayload, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == payload.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    if db_user.is_email_verified:
        return {"ok": True, "message": "Already verified"}

    if not db_user.email_verification_token_hash:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    if datetime.now(timezone.utc) > db_user.email_verification_expires_at:
        raise HTTPException(status_code=400, detail="Verification link expired")

    if hash_token(payload.token) != db_user.email_verification_token_hash:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    db_user.is_email_verified = True
    db_user.email_verified_at = datetime.now(timezone.utc)
    db_user.email_verification_token_hash = None
    db_user.email_verification_expires_at = None

    db.commit()
    return {"ok": True}

# ======================================================
# Resend verification
# ======================================================

class ResendVerificationPayload(BaseModel):
    email: EmailStr

@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationPayload, db: Session = Depends(get_db)):
    # generic response to prevent email enumeration
    response = {"ok": True, "message": "If that email exists, a verification link was generated."}

    db_user = db.query(User).filter(User.email == payload.email).first()
    if not db_user:
        return response

    if db_user.is_email_verified:
        return {"ok": True, "message": "Email already verified"}

    raw_token, token_hash, expires_at = make_verify_token()
    db_user.email_verification_token_hash = token_hash
    db_user.email_verification_expires_at = expires_at
    db_user.email_verified_at = None

    db.commit()

    # DEV ONLY: log token so you can test before email is wired
    if os.getenv("ENV", "prod") != "prod":
        print(f"[DEV] Email verify token for {db_user.email}: {raw_token}")

    return response
