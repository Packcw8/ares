import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from db import get_db
from models import User

# Load SECRET_KEY and ALGORITHM from .env
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"🔐 Raw token received: {token}")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"✅ Decoded JWT payload: {payload}")
        user_id: int = payload.get("sub")
        if user_id is None:
            print("❌ Token has no 'sub'")
            raise credentials_exception
    except JWTError as e:
        print(f"❌ JWT decode error: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"❌ No user found with ID: {user_id}")
        raise credentials_exception

    print(f"✅ Authenticated user: {user.email} (ID: {user.id})")
    return user
