from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from db import engine, Base, get_db
from models import User
from schemas import UserCreate
import uvicorn

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    return db.query(User).all()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
