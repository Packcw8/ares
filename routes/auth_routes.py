from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.schemas import UserCreate, UserOut, UserLogin
from models.user import User
from db import get_db
from utils.auth import hash_password, authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == user.email).first()
    existing_username = db.query(User).filter(User.username == user.username).first()

    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Always set official users as unverified
    is_verified = False if user.role == "official" else True

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password),
        role=user.role,
        is_verified=is_verified
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ✅ include role in the token payload
    access_token = create_access_token(data={
        "sub": str(db_user.id),
        "role": db_user.role
    })

    return {"access_token": access_token, "token_type": "bearer"}

