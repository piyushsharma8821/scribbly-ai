from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.db import users_collection
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

class User(BaseModel):
    username: str
    password: str

@router.post("/signup")
async def signup(user: User):
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = pwd_context.hash(user.password)
    user_dict = {"username": user.username, "password": hashed_pw}
    await users_collection.insert_one(user_dict)
    return {"message": "User created successfully"}


@router.post("/login")
async def login(user: User):
    db_user = await users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minute=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)