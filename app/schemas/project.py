from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict
from app.schemas.user import UserOut

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by: Optional[int]
    created_at: datetime
    is_deleted: bool

class ProjectMemberCreate(BaseModel):
    user_id: int

class ProjectMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    user_id: int
    user: Optional[UserOut] = None

class ProjectAnalytics(BaseModel):
    project_id: int
    name: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    workload_distribution: Dict[str, int]
