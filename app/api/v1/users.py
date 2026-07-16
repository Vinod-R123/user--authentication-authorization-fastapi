from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.crud import user as crud_user
from app.crud import activity_log as crud_activity

router = APIRouter()

@router.get("", response_model=List[UserOut])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    return crud_user.get_users(db, skip=skip, limit=limit)

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    user_in: UserCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    db_user = crud_user.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    new_user = crud_user.create_user(db, user_in=user_in)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Admin Create User",
        details=f"Admin created user: {new_user.email} with role: {new_user.role}"
    )
    return new_user

@router.put("/{id}", response_model=UserOut)
def update_user_by_admin(
    id: int,
    user_in: UserUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    db_user = crud_user.get_user(db, user_id=id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    updated_user = crud_user.update_user(db, db_user=db_user, user_in=user_in)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Admin Update User",
        details=f"Admin updated user ID: {id}"
    )
    return updated_user

@router.delete("/{id}", response_model=UserOut)
def delete_user_by_admin(
    id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    db_user = crud_user.get_user(db, user_id=id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    deleted_user = crud_user.delete_user(db, user_id=id)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Admin Delete User",
        details=f"Admin soft deleted user ID: {id}"
    )
    return deleted_user
