import os
from dotenv import load_dotenv
import httpx

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.database import get_db
from database.models import User
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from auth.auth_handler import create_token

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET=os.getenv("GITHUB_CLIENT_SECRET")

@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = User(
        username=request.username,
        email=request.email,
        password_hash=pwd_context.hash(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token)


@router.get("/github/login")
def github_login():
    return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri=https://wraith-6efg.onrender.com/auth/github/callback")


@router.get("/github/callback")
def github_callback(code: str, db:Session= Depends(get_db)):
    token_res = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
    )
    access_token = token_res.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub auth failed")
    
    user_res = httpx.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    github_user = user_res.json()
    github_id = str(github_user["id"])
    username = github_user.get("login")
    email = github_user.get("email")

    user = db.query(User).filter(User.github_id == github_id).first()
    if not user:
        user = User(
            username=username,
            email=email,
            github_id=github_id,
            password_hash=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token({"sub": str(user.id), "username": user.username})
    return {"access_token": token}