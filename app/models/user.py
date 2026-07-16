import enum
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    MEMBER = "Member"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.MEMBER.value)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    projects_created = relationship("Project", back_populates="creator")
    memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    tasks_assigned = relationship("Task", back_populates="assignee")
    comments = relationship("Comment", back_populates="user")
