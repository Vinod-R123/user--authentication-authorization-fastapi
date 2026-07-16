from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    full_name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.MEMBER

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_deleted: bool
