from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.activity_log import ActivityLog

def create_activity_log(db: Session, user_id: Optional[int], action: str, details: Optional[str] = None) -> ActivityLog:
    db_log = ActivityLog(user_id=user_id, action=action, details=details)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_activity_logs(db: Session, skip: int = 0, limit: int = 100) -> List[ActivityLog]:
    return db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()
