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
import requests
from urllib.parse import urlencode

router = APIRouter(prefix="/auth", tags=["auth"])

# ======================================================
# Config (ENV VARS)
# ======================================================
# Required for email sending:
#   RESEND_API_KEY=...
#   FRONTEND_URL=https://www.aresjustice.com
# Optional:
#   FROM_EMAIL=no-reply@aresjustice.com  (or onboarding@resend.dev for testing)
#   REQUIRE_VERIFIED_EMAIL_ON_LOGIN=false|true

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
REQUIRE_VERIFIED_EMAIL_ON_LOGIN = os.getenv("REQUIRE_VERIFIED_EMAIL_ON_LOGIN", "false").lower() == "true"

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

def build_verify_link(email: str, token: str) -> str:
    qs = urlencode({"email": email, "token": token})
    return f"{FRONTEND_URL}/verify-email?{qs}"

def send_verification_email(to_email: str, token: str) -> None:
    """
    Sends a verification email via Resend.
    If RESEND_API_KEY is missing, we do NOT crash signup/resend in prod;
    we log and continue so you can deploy safely while wiring provider.
    """
    verify_link = build_verify_link(to_email, token)

    if not RESEND_API_KEY:
        # Don’t break auth flows just because email isn’t wired yet
        print("[WARN] RESEND_API_KEY not set; skipping verification email send.")
        print(f"[WARN] Verification link (dev): {verify_link}")
        return

    payload = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": "Verify your email for ARES",
        "html": f"""
        <div style="font-family:Arial,sans-serif;line-height:1.5">
          <h2>Verify your email</h2>
          <p>Click the button below to verify your email for ARES.</p>
          <p>
            <a href="{verify_link}"
               style="display:inline-block;padding:10px 16px;background:#1c2b4a;color:white;text-decoration:none;border-radius:6px;">
              Verify Email
            </a>
          </p>
          <p>If the button doesn’t work, paste this link into your browser:</p>
          <p>{verify_link}</p>
        </div>
        """
    }

    r = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if r.status_code >= 400:
        # Log and continue — don’t block signup
        print(f"[ERROR] Resend failed: {r.status_code} {r.text}")
        return

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

    # keep existing official verification behavior (admin verification)
    is_verified = False if user.role == "official" else True

    # generate email verification token (store hash only)
    raw_token, token_hash, expires_at = make_verify_token()

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

    # send verification email (non-blocking behavior)
    send_verification_email(new_user.email, raw_token)

    return new_user

# ======================================================
# Login
# ======================================================

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if REQUIRE_VERIFIED_EMAIL_ON_LOGIN and not db_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

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

    if not db_user.email_verification_token_hash or not db_user.email_verification_expires_at:
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
    response = {"ok": True, "message": "If that email exists, a verification link was sent."}

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

    send_verification_email(db_user.email, raw_token)
    return response
