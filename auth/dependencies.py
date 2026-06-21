from fastapi import Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User
from auth.auth_handler import verify_token
from typing import Optional

security = HTTPBearer(auto_error=False)

def get_current_user(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if not authorization:
        print("failes here at auth none")
        return None
    token = authorization.credentials
    payload = verify_token(token)
    print("PAYLOAD:",payload)
    if not payload:
        print("payload is none")
        return None
    user = db.query(User).filter(User.id == payload["sub"]).first()
    return user