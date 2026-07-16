from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from app.schemas.user import UserOut

class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    action: str
    timestamp: datetime
    details: Optional[str]
    user: Optional[UserOut] = None
