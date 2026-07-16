def test_signup(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "New User",
            "email": "newuser@example.com",
            "password": "strongpassword",
            "role": "Member"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "Member"

def test_signup_existing_email(client):
    # Try signing up with test admin email
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "New Admin",
            "email": "admin_test@example.com",
            "password": "password",
            "role": "Admin"
        }
    )
    assert response.status_code == 400

def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_test@example.com", "password": "password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 400

def test_me_authorized(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin_test@example.com"
    assert data["role"] == "Admin"

def test_me_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
