from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.PENDING
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    project_id: int

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    project_id: Optional[int] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
