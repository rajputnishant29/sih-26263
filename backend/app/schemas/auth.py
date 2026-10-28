from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserSummary"


class UserSummary(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None

    class Config:
        from_attributes = True


class DemoRoleSwitchRequest(BaseModel):
    target_role: str
    institution_id: Optional[int] = None


Token.model_rebuild()
