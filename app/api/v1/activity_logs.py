from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.activity_log import ActivityLogOut
from app.crud import activity_log as crud_activity

router = APIRouter()

@router.get("", response_model=List[ActivityLogOut])
def read_activity_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    return crud_activity.get_activity_logs(db, skip=skip, limit=limit)
