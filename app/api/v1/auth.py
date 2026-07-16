from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut
from app.crud import user as crud_user
from app.crud import activity_log as crud_activity
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = crud_user.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    user = crud_user.create_user(db, user_in=user_in)
    crud_activity.create_activity_log(
        db, 
        user_id=user.id, 
        action="User Signup", 
        details=f"User signed up: {user.email} with role: {user.role}"
    )
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    access_token = create_access_token(subject=user.id)
    crud_activity.create_activity_log(
        db, 
        user_id=user.id, 
        action="User Login", 
        details="User logged in successfully"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
