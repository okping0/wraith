from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.database import get_db
from database.models import User
from auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from auth.auth_handler import create_token

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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