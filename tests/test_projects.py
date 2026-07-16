import pytest

def test_create_project_admin(client, admin_headers):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Admin Project", "description": "Created by Admin"},
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Admin Project"

def test_create_project_manager(client, manager_headers):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Manager Project", "description": "Created by Manager"},
        headers=manager_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Manager Project"

def test_create_project_member_forbidden(client, member_headers):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Member Project", "description": "Created by Member"},
        headers=member_headers
    )
    assert response.status_code == 403

def test_list_projects(client, admin_headers, manager_headers, member_headers):
    # 1. Admin creates project
    client.post(
        "/api/v1/projects",
        json={"name": "P1", "description": "D1"},
        headers=admin_headers
    )
    # 2. Manager creates project
    client.post(
        "/api/v1/projects",
        json={"name": "P2", "description": "D2"},
        headers=manager_headers
    )

    # 3. Admin lists (should see all projects)
    r_admin = client.get("/api/v1/projects", headers=admin_headers)
    assert r_admin.status_code == 200
    assert len(r_admin.json()) >= 2

    # 4. Member lists (should see nothing because they aren't added to any project)
    r_member = client.get("/api/v1/projects", headers=member_headers)
    assert r_member.status_code == 200
    assert len(r_member.json()) == 0

def test_project_memberships(client, manager_headers, member_headers, db):
    from app.models.user import User
    # 1. Manager creates a project
    r_proj = client.post(
        "/api/v1/projects",
        json={"name": "Shared Project", "description": "Desc"},
        headers=manager_headers
    )
    proj_id = r_proj.json()["id"]

    # Get member user_id
    member_user = db.query(User).filter(User.email == "member_test@example.com").first()

    # 2. Add Member to project
    r_add = client.post(
        f"/api/v1/projects/{proj_id}/members",
        json={"user_id": member_user.id},
        headers=manager_headers
    )
    assert r_add.status_code == 201

    # 3. Now member lists projects, they should see "Shared Project"
    r_list = client.get("/api/v1/projects", headers=member_headers)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1
    assert r_list.json()[0]["id"] == proj_id

    # 4. Delete member from project
    r_del = client.delete(
        f"/api/v1/projects/{proj_id}/members/{member_user.id}",
        headers=manager_headers
    )
    assert r_del.status_code == 204

    # 5. Member lists again, should be empty
    r_list_after = client.get("/api/v1/projects", headers=member_headers)
    assert len(r_list_after.json()) == 0

def test_delete_project_rbac(client, admin_headers, manager_headers):
    # Manager creates a project
    r_proj = client.post(
        "/api/v1/projects",
        json={"name": "To Delete Project", "description": "Desc"},
        headers=manager_headers
    )
    proj_id = r_proj.json()["id"]

    # Manager attempts to delete project (should fail - only Admin can delete)
    r_del_mgr = client.delete(f"/api/v1/projects/{proj_id}", headers=manager_headers)
    assert r_del_mgr.status_code == 403

    # Admin deletes project (should succeed)
    r_del_adm = client.delete(f"/api/v1/projects/{proj_id}", headers=admin_headers)
    assert r_del_adm.status_code == 200
    assert r_del_adm.json()["is_deleted"] is True
