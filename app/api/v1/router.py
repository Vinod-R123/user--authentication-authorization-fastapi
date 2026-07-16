from fastapi import APIRouter
from app.api.v1 import auth, projects, tasks, users, activity_logs

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(activity_logs.router, prefix="/activity-logs", tags=["Activity Logs"])
