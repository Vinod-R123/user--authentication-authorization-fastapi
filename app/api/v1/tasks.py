from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role, check_project_access, check_task_access
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.schemas.comment import CommentCreate, CommentOut
from app.crud import task as crud_task
from app.crud import project as crud_project
from app.crud import comment as crud_comment
from app.crud import activity_log as crud_activity

router = APIRouter()

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN.value, UserRole.MANAGER.value])),
    db: Session = Depends(get_db)
):
    # Verify access to the project
    check_project_access(db, project_id=task_in.project_id, user=current_user)
    
    # Verify that the assignee is a member of the project
    if task_in.assigned_to is not None:
        if not crud_project.is_project_member(db, project_id=task_in.project_id, user_id=task_in.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of the project"
            )
            
    task = crud_task.create_task(db, task_in=task_in)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Create Task",
        details=f"Task '{task.title}' (ID: {task.id}) created under Project ID: {task.project_id}"
    )
    return task

@router.get("", response_model=List[TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # If project_id is provided, verify access to that specific project
    if project_id is not None:
        check_project_access(db, project_id=project_id, user=current_user)
        return crud_task.get_tasks(
            db, project_id=project_id, assigned_to=assigned_to, 
            status=status, priority=priority, skip=skip, limit=limit
        )
    
    # If project_id is not provided, fetch all projects user is authorized to access
    auth_projects = crud_project.get_projects(db, user_id=current_user.id, role=current_user.role, limit=1000)
    auth_project_ids = [p.id for p in auth_projects]
    
    # Perform database filtering using the authorized project IDs list
    query = db.query(Task).filter(Task.is_deleted == False, Task.project_id.in_(auth_project_ids))
    
    if assigned_to is not None:
        query = query.filter(Task.assigned_to == assigned_to)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
        
    return query.offset(skip).limit(limit).all()

@router.get("/{id}", response_model=TaskOut)
def get_task_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify access to the task (via its project)
    task = check_task_access(db, task_id=id, user=current_user)
    return task

@router.put("/{id}", response_model=TaskOut)
def update_task(
    id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify access to the task (via its project)
    task = check_task_access(db, task_id=id, user=current_user)
    
    # RBAC:
    # 1. Members can only update status and MUST be the assignee
    if current_user.role == UserRole.MEMBER.value:
        if task.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tasks assigned to you"
            )
        
        # Check if Member attempted to modify other fields
        update_data = task_in.model_dump(exclude_unset=True)
        if any(k != "status" for k in update_data.keys()):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Members can only update the task status"
            )
            
    # 2. Managers and Admins can update any field.
    # Check project membership constraint on assignee update
    if task_in.assigned_to is not None:
        proj_id = task_in.project_id if task_in.project_id is not None else task.project_id
        if not crud_project.is_project_member(db, project_id=proj_id, user_id=task_in.assigned_to):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of the project"
            )
            
    updated_task = crud_task.update_task(db, db_task=task, task_in=task_in)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Update Task",
        details=f"Task ID: {id} updated"
    )
    return updated_task

@router.delete("/{id}", response_model=TaskOut)
def delete_task(
    id: int,
    current_user: User = Depends(require_role([UserRole.ADMIN.value, UserRole.MANAGER.value])),
    db: Session = Depends(get_db)
):
    # Verify access to task project
    task = check_task_access(db, task_id=id, user=current_user)
    
    deleted_task = crud_task.delete_task(db, task_id=id)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Delete Task",
        details=f"Task ID: {id} soft deleted"
    )
    return deleted_task

# TASK COMMENTS ENDPOINTS

@router.post("/{id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project access
    check_task_access(db, task_id=id, user=current_user)
    
    comment = crud_comment.create_comment(db, comment_in=comment_in, task_id=id, user_id=current_user.id)
    crud_activity.create_activity_log(
        db,
        user_id=current_user.id,
        action="Add Comment",
        details=f"Added comment on task ID: {id}"
    )
    return comment

@router.get("/{id}/comments", response_model=List[CommentOut])
def get_comments(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify project access
    check_task_access(db, task_id=id, user=current_user)
    return crud_comment.get_comments_by_task(db, task_id=id)
