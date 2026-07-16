from sqlalchemy.orm import Session
from typing import List
from app.models.comment import Comment
from app.schemas.comment import CommentCreate

def create_comment(db: Session, comment_in: CommentCreate, task_id: int, user_id: int) -> Comment:
    db_comment = Comment(
        task_id=task_id,
        user_id=user_id,
        content=comment_in.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_task(db: Session, task_id: int) -> List[Comment]:
    return db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at.asc()).all()
