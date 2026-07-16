from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id, User.is_deleted == False).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email, User.is_deleted == False).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).filter(User.is_deleted == False).offset(skip).limit(limit).all()

def create_user(db: Session, user_in: UserCreate) -> User:
    db_user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, user_in: UserUpdate) -> User:
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        password = update_data.pop("password")
        db_user.password_hash = get_password_hash(password)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.is_deleted = True
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    return db_user
