from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role, check_project_access
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut, ProjectMemberOut, ProjectMemberCreate, ProjectAnalytics
from app.crud import project as crud_project
from app.crud import user as crud_user
from app.crud import activity_log as crud_activity

router = APIRouter()

@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN.value, UserRole.MANAGER.value])),
    db: Session = Depends(get_db)
):
    project = crud_project.create_project(db, project_in=project_in, created_by_id=current_user.id)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Create Project",
        details=f"Project '{project.name}' (ID: {project.id}) created"
    )
    return project

@router.get("", response_model=List[ProjectOut])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Admins get all; Managers/Members get owned or member projects
    return crud_project.get_projects(db, user_id=current_user.id, role=current_user.role, skip=skip, limit=limit)

@router.get("/{id}", response_model=ProjectOut)
def get_project_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = check_project_access(db, project_id=id, user=current_user)
    return project

@router.put("/{id}", response_model=ProjectOut)
def update_project(
    id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = check_project_access(db, project_id=id, user=current_user)
    
    # RBAC: Only Admin or a Manager who created the project or is a member can update it
    if current_user.role == UserRole.MEMBER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Members cannot update project details"
        )
        
    updated_project = crud_project.update_project(db, db_project=project, project_in=project_in)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Update Project",
        details=f"Project ID: {id} updated metadata"
    )
    return updated_project

@router.delete("/{id}", response_model=ProjectOut)
def delete_project(
    id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN.value])),
    db: Session = Depends(get_db)
):
    project = crud_project.get_project(db, project_id=id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    deleted_project = crud_project.delete_project(db, project_id=id)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Delete Project",
        details=f"Project ID: {id} soft deleted"
    )
    return deleted_project

# PROJECT MEMBERS ENDPOINTS

@router.post("/{id}/members", response_model=ProjectMemberOut, status_code=status.HTTP_201_CREATED)
def add_project_member(
    id: int,
    member_in: ProjectMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = check_project_access(db, project_id=id, user=current_user)
    
    # RBAC: Only Admin or project Creator/Manager can add members
    if current_user.role == UserRole.MEMBER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Members cannot manage project memberships"
        )
        
    # Verify the user to add actually exists
    user_to_add = crud_user.get_user(db, user_id=member_in.user_id)
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user to add not found"
        )
        
    membership = crud_project.add_project_member(db, project_id=id, user_id=member_in.user_id)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Add Project Member",
        details=f"User ID {member_in.user_id} added to project {id}"
    )
    return membership

@router.get("/{id}/members", response_model=List[ProjectMemberOut])
def list_project_members(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Checks if user has access to project to see its members
    check_project_access(db, project_id=id, user=current_user)
    return crud_project.get_project_members(db, project_id=id)

@router.delete("/{id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = check_project_access(db, project_id=id, user=current_user)
    
    # RBAC: Only Admin or project Creator/Manager can remove members
    if current_user.role == UserRole.MEMBER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Members cannot manage project memberships"
        )
        
    removed = crud_project.remove_project_member(db, project_id=id, user_id=user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found"
        )
        
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Remove Project Member",
        details=f"User ID {user_id} removed from project {id}"
    )
    return

# ANALYTICS ENDPOINT

@router.get("/{id}/analytics", response_model=ProjectAnalytics)
def get_project_analytics(
    id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN.value, UserRole.MANAGER.value])),
    db: Session = Depends(get_db)
):
    # Verify access to the project
    project = check_project_access(db, project_id=id, user=current_user)
    
    # Fetch non-deleted tasks
    tasks = db.query(Task).filter(Task.project_id == id, Task.is_deleted == False).all()
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED.value)
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING.value)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS.value)
    
    workload = {}
    for t in tasks:
        # Load assignee if exists
        if t.assignee:
            name_key = t.assignee.email
            workload[name_key] = workload.get(name_key, 0) + 1
        else:
            workload["Unassigned"] = workload.get("Unassigned", 0) + 1
            
    return {
        "project_id": project.id,
        "name": project.name,
        "total_tasks": total,
        "completed_tasks": completed,
        "pending_tasks": pending,
        "in_progress_tasks": in_progress,
        "workload_distribution": workload
    }
