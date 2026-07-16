from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.schemas.user import UserOut

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentOut(CommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: Optional[int]
    created_at: datetime
    user: Optional[UserOut] = None
