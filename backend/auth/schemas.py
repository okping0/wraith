from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain atleast one uppercase letter")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain atleast one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain atleast one digit")
        if len(v) < 8:
            raise ValueError("Password must be atleast 8 characters")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"