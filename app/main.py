from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy.orm import Session

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# Seed default accounts for testing convenience
def seed_data():
    db: Session = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if not admin_exists:
            # Seed Admin
            admin = User(
                full_name="System Administrator",
                email="admin@example.com",
                password_hash=get_password_hash("AdminPassword123"),
                role=UserRole.ADMIN.value
            )
            db.add(admin)
            
            # Seed Manager
            manager = User(
                full_name="Project Manager",
                email="manager@example.com",
                password_hash=get_password_hash("ManagerPassword123"),
                role=UserRole.MANAGER.value
            )
            db.add(manager)
            
            # Seed Member
            member = User(
                full_name="Team Member",
                email="member@example.com",
                password_hash=get_password_hash("MemberPassword123"),
                role=UserRole.MEMBER.value
            )
            db.add(member)
            
            db.commit()
            print("Successfully seeded initial Admin, Manager, and Member test accounts.")
    except Exception as e:
        print(f"Failed to seed initial data: {e}")
    finally:
        db.close()

seed_data()

app = FastAPI(
    title="Project Management API with RBAC",
    description=(
        "A secure, role-based backend for managing projects, team members, tasks, and task comments. "
        "Built with FastAPI, SQLAlchemy, SQLite, and JWT authentication."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to the Project Management API with RBAC",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "version": "1.0.0",
        "default_accounts": {
            "admin": "admin@example.com / AdminPassword123",
            "manager": "manager@example.com / ManagerPassword123",
            "member": "member@example.com / MemberPassword123"
        }
    }
