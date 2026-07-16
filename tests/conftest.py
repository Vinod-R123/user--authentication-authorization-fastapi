import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole

# Separate test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="db")
def db_fixture():
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    
    # Seed users for test runs
    admin = db.query(User).filter(User.email == "admin_test@example.com").first()
    if not admin:
        u_admin = User(
            full_name="Test Admin",
            email="admin_test@example.com",
            password_hash=get_password_hash("password"),
            role=UserRole.ADMIN.value
        )
        db.add(u_admin)
        
        u_mgr = User(
            full_name="Test Manager",
            email="manager_test@example.com",
            password_hash=get_password_hash("password"),
            role=UserRole.MANAGER.value
        )
        db.add(u_mgr)
        
        u_mem = User(
            full_name="Test Member",
            email="member_test@example.com",
            password_hash=get_password_hash("password"),
            role=UserRole.MEMBER.value
        )
        db.add(u_mem)
        
        u_mem2 = User(
            full_name="Test Member 2",
            email="member_test2@example.com",
            password_hash=get_password_hash("password"),
            role=UserRole.MEMBER.value
        )
        db.add(u_mem2)
        db.commit()

    yield db
    db.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(name="client")
def client_fixture(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_headers(db):
    user = db.query(User).filter(User.email == "admin_test@example.com").first()
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def manager_headers(db):
    user = db.query(User).filter(User.email == "manager_test@example.com").first()
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def member_headers(db):
    user = db.query(User).filter(User.email == "member_test@example.com").first()
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def member2_headers(db):
    user = db.query(User).filter(User.email == "member_test2@example.com").first()
    token = create_access_token(subject=user.id)
    return {"Authorization": f"Bearer {token}"}
