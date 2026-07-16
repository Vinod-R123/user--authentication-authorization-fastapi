from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.query(Task).filter(Task.id == task_id, Task.is_deleted == False).first()

def get_tasks(
    db: Session,
    project_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Task]:
    query = db.query(Task).filter(Task.is_deleted == False)
    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if assigned_to is not None:
        query = query.filter(Task.assigned_to == assigned_to)
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    return query.offset(skip).limit(limit).all()

def create_task(db: Session, task_in: TaskCreate) -> Task:
    db_task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
        assigned_to=task_in.assigned_to,
        project_id=task_in.project_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, db_task: Task, task_in: TaskUpdate) -> Task:
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int) -> Optional[Task]:
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task:
        db_task.is_deleted = True
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
    return db_task
