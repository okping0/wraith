import os
from dotenv import load_dotenv
import httpx
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.database import get_db
from database.models import User
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from auth.auth_handler import create_token
from auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET=os.getenv("GITHUB_CLIENT_SECRET")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def validate_password(pw: str) -> Optional[str]:
    if len(pw) < 8:
        return "Password must be at least 8 characters"
    if len(pw.encode()) > 72:
        return "Password is too long (max 72 characters)"
    if not re.search(r"[a-z]", pw):
        return "Password needs a lowercase letter"
    if not re.search(r"[A-Z]", pw):
        return "Password needs an uppercase letter"
    if not re.search(r"\d", pw):
        return "Password needs a number"
    if not re.search(r"[^A-Za-z0-9]", pw):
        return "Password needs a special character"
    return None


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", request.email):
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    err = validate_password(request.password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    
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
    if user and not user.password_hash:
        raise HTTPException(
            status_code=400,
            detail="This account uses GitHub. Click 'Continue with GitHub'.",
        )
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    token = create_token({"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token)


@router.get("/github/login")
def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={BACKEND_URL}/auth/github/callback"
        "&scope=read:user%20user:email"
        "&prompt=select_account"
        )


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

    if not email:
        emails = httpx.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
        ).json()
        if isinstance(emails, list):
            email = next(
                (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                None,
            )

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
    return RedirectResponse(f"{FRONTEND_URL}/app?token={token}")


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }