from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from schemas.schemas import UserCreate, UserOut, UserLogin
from models.user import User
from models.password_reset import PasswordResetToken
from db import get_db
from utils.auth import (
    hash_password,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from utils.email import send_verification_email, send_password_reset_email

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

router = APIRouter(prefix="/auth", tags=["auth"])

# ======================================================
# Config
# ======================================================
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")

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
            "http://localhost:3000",
        ] else "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
    }
    return JSONResponse(content={"message": "Signup CORS OK"}, headers=headers)

# ======================================================
# Signup
# ======================================================
@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    username = user.username.lower().strip()
    email = user.email.lower().strip()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    raw_token, token_hash, expires_at = make_verify_token()

    if user.role == "official":
        role = "official_pending"
        is_verified = False
    else:
        role = "citizen"
        is_verified = True

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(user.password),
        role=role,
        is_verified=is_verified,
        is_email_verified=False,

        full_name=user.full_name,
        title=user.title,
        agency=user.agency,
        official_email=user.official_email,
        state=user.state,
        jurisdiction=user.jurisdiction,

        email_verification_token_hash=token_hash,
        email_verification_expires_at=expires_at,
        email_verified_at=None,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_verification_email(new_user.email, raw_token)
    return new_user

# ======================================================
# Login (username OR email)
# ======================================================
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.identifier, user.password)

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username/email or password",
        )

    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role}
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ======================================================
# Forgot Password (Recovery)
# ======================================================
class ForgotPasswordPayload(BaseModel):
    identifier: str

@router.post("/forgot-password", status_code=200)
def forgot_password(
    payload: ForgotPasswordPayload,
    db: Session = Depends(get_db),
):
    """
    Accepts email OR username.
    Always returns success to prevent account enumeration.
    """

    identifier = payload.identifier.lower().strip()

    user = (
        db.query(User)
        .filter(
            (User.email == identifier) |
            (User.username == identifier)
        )
        .first()
    )

    response = {
        "message": "If an account exists, a reset link has been sent."
    }

    if not user:
        return response

    # Invalidate any previous unused tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).delete()

    raw_token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        used=False,
    )

    db.add(reset_token)
    db.commit()

    send_password_reset_email(
        to_email=user.email,
        token=raw_token,
    )

    return response
# ======================================================
# Reset Password (Final Step)
# ======================================================
class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password", status_code=200)
def reset_password(
    payload: ResetPasswordPayload,
    db: Session = Depends(get_db),
):
    """
    Resets a user's password using a one-time token.
    """

    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
        )
        .first()
    )

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset link",
        )

    if datetime.now(timezone.utc) > reset_token.expires_at:
        raise HTTPException(
            status_code=400,
            detail="Reset link has expired",
        )

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid reset request",
        )

    # 🔒 Update password
    user.hashed_password = hash_password(payload.new_password)

    # 🔒 Invalidate token immediately
    reset_token.used = True
    reset_token.used_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "message": "Password reset successful. You may now log in."
    }


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
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    if user.is_email_verified:
        return {"ok": True, "message": "Already verified"}

    if not user.email_verification_token_hash or not user.email_verification_expires_at:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    if datetime.now(timezone.utc) > user.email_verification_expires_at:
        raise HTTPException(status_code=400, detail="Verification link expired")

    if hash_token(payload.token) != user.email_verification_token_hash:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None
    db.commit()

    return {"ok": True, "message": "Email verified"}

# ======================================================
# Resend verification
# ======================================================
class ResendVerificationPayload(BaseModel):
    email: EmailStr

@router.post("/resend-verification")
def resend_verification(
    payload: ResendVerificationPayload,
    db: Session = Depends(get_db),
):
    response = {
        "ok": True,
        "message": "If the email exists, a verification link was sent",
    }

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or user.is_email_verified:
        return response

    raw_token, token_hash, expires_at = make_verify_token()
    user.email_verification_token_hash = token_hash
    user.email_verification_expires_at = expires_at
    user.email_verified_at = None
    db.commit()

    send_verification_email(user.email, raw_token)
    return response
