import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class TaskStatus(str, enum.Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"

class TaskPriority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=TaskStatus.PENDING.value)
    priority = Column(String, nullable=False, default=TaskPriority.MEDIUM.value)
    due_date = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks_assigned")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
