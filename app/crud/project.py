from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.project import Project, ProjectMember
from app.models.user import UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate

def get_project(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()

def get_projects(db: Session, user_id: int, role: str, skip: int = 0, limit: int = 100) -> List[Project]:
    if role == UserRole.ADMIN.value:
        return db.query(Project).filter(Project.is_deleted == False).offset(skip).limit(limit).all()
    
    # Manager and Member see projects they created OR are members of
    return db.query(Project).join(
        ProjectMember, ProjectMember.project_id == Project.id, isouter=True
    ).filter(
        Project.is_deleted == False,
        or_(
            Project.created_by == user_id,
            ProjectMember.user_id == user_id
        )
    ).distinct().offset(skip).limit(limit).all()

def create_project(db: Session, project_in: ProjectCreate, created_by_id: int) -> Project:
    db_project = Project(
        name=project_in.name,
        description=project_in.description,
        created_by=created_by_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Automatically add creator as a member of the project as well for consistency
    add_project_member(db, db_project.id, created_by_id)
    
    return db_project

def update_project(db: Session, db_project: Project, project_in: ProjectUpdate) -> Project:
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int) -> Optional[Project]:
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project:
        db_project.is_deleted = True
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
    return db_project

def add_project_member(db: Session, project_id: int, user_id: int) -> ProjectMember:
    # Check if membership already exists to prevent duplicate constraint violation
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    if existing:
        return existing
        
    db_member = ProjectMember(project_id=project_id, user_id=user_id)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def remove_project_member(db: Session, project_id: int, user_id: int) -> bool:
    db_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    if db_member:
        db.delete(db_member)
        db.commit()
        return True
    return False

def get_project_members(db: Session, project_id: int) -> List[ProjectMember]:
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

def is_project_member(db: Session, project_id: int, user_id: int) -> bool:
    return db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first() is not None
