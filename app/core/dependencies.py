from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.task import Task
from app.crud import user as crud_user
from app.crud import project as crud_project
from app.crud import task as crud_task

# The tokenUrl matches our login endpoint path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = crud_user.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user

def require_role(allowed_roles: list[str]):
    def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return dependency

def check_project_access(db: Session, project_id: int, user: User) -> Project:
    project = crud_project.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    # Admin has access to all projects
    if user.role == UserRole.ADMIN.value:
        return project
    # Owner (creator) has access
    if project.created_by == user.id:
        return project
    # Members have access
    if crud_project.is_project_member(db, project_id=project.id, user_id=user.id):
        return project
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this project"
    )

def check_task_access(db: Session, task_id: int, user: User) -> Task:
    task = crud_task.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    # Tasks are scoped under projects, check project access first
    check_project_access(db, task.project_id, user)
    return task
