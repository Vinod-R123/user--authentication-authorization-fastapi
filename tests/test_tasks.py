import pytest
from app.models.user import User

def test_create_task_validation(client, manager_headers, member_headers, db):
    # 1. Manager creates a project
    r_proj = client.post(
        "/api/v1/projects",
        json={"name": "Task Project", "description": "D"},
        headers=manager_headers
    )
    proj_id = r_proj.json()["id"]

    # Get users
    member_user = db.query(User).filter(User.email == "member_test@example.com").first()
    member2_user = db.query(User).filter(User.email == "member_test2@example.com").first()

    # Add member_user (Member 1) to project members, but NOT member2_user
    client.post(
        f"/api/v1/projects/{proj_id}/members",
        json={"user_id": member_user.id},
        headers=manager_headers
    )

    # 2. Try creating task assigning to member2_user (should fail - not project member)
    r_task_fail = client.post(
        "/api/v1/tasks",
        json={
            "title": "Unassigned Task",
            "description": "Fail assignment",
            "assigned_to": member2_user.id,
            "project_id": proj_id
        },
        headers=manager_headers
    )
    assert r_task_fail.status_code == 400

    # 3. Create task assigning to member_user (should succeed - member is in project)
    r_task_success = client.post(
        "/api/v1/tasks",
        json={
            "title": "Valid Task",
            "description": "Pass assignment",
            "assigned_to": member_user.id,
            "project_id": proj_id
        },
        headers=manager_headers
    )
    assert r_task_success.status_code == 201
    task_id = r_task_success.json()["id"]

    # 4. Member tries to create a task (should fail - members cannot create tasks)
    r_task_member = client.post(
        "/api/v1/tasks",
        json={
            "title": "Member Created Task",
            "project_id": proj_id
        },
        headers=member_headers
    )
    assert r_task_member.status_code == 403

def test_update_task_rbac(client, manager_headers, member_headers, member2_headers, db):
    # 1. Manager creates project
    r_proj = client.post(
        "/api/v1/projects",
        json={"name": "Update Task Project", "description": "D"},
        headers=manager_headers
    )
    proj_id = r_proj.json()["id"]

    # Get users
    member_user = db.query(User).filter(User.email == "member_test@example.com").first()
    member2_user = db.query(User).filter(User.email == "member_test2@example.com").first()

    # Add both members to the project
    client.post(f"/api/v1/projects/{proj_id}/members", json={"user_id": member_user.id}, headers=manager_headers)
    client.post(f"/api/v1/projects/{proj_id}/members", json={"user_id": member2_user.id}, headers=manager_headers)

    # 2. Manager creates task and assigns to member_user
    r_task = client.post(
        "/api/v1/tasks",
        json={
            "title": "Action Task",
            "assigned_to": member_user.id,
            "project_id": proj_id
        },
        headers=manager_headers
    )
    task_id = r_task.json()["id"]

    # 3. Member 2 tries to update status (should fail - not assigned to them)
    r_up_mem2 = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "In Progress"},
        headers=member2_headers
    )
    assert r_up_mem2.status_code == 403

    # 4. Member 1 (assignee) tries to update title (should fail - members can only update status)
    r_up_title = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Hack title"},
        headers=member_headers
    )
    assert r_up_title.status_code == 403

    # 5. Member 1 (assignee) updates status to "Completed" (should succeed)
    r_up_status = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "Completed"},
        headers=member_headers
    )
    assert r_up_status.status_code == 200
    assert r_up_status.json()["status"] == "Completed"

    # 6. Manager updates title (should succeed)
    r_up_mgr = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Manager Updated Title"},
        headers=manager_headers
    )
    assert r_up_mgr.status_code == 200
    assert r_up_mgr.json()["title"] == "Manager Updated Title"

def test_task_commenting(client, manager_headers, member_headers, db):
    # Manager creates project
    r_proj = client.post(
        "/api/v1/projects",
        json={"name": "Comment Project", "description": "D"},
        headers=manager_headers
    )
    proj_id = r_proj.json()["id"]

    member_user = db.query(User).filter(User.email == "member_test@example.com").first()
    client.post(f"/api/v1/projects/{proj_id}/members", json={"user_id": member_user.id}, headers=manager_headers)

    # Manager creates task
    r_task = client.post(
        "/api/v1/tasks",
        json={"title": "Task with Comment", "project_id": proj_id},
        headers=manager_headers
    )
    task_id = r_task.json()["id"]

    # Member comments on task
    r_comm = client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "I am working on this task now."},
        headers=member_headers
    )
    assert r_comm.status_code == 201
    assert r_comm.json()["content"] == "I am working on this task now."

    # Get comments
    r_list = client.get(f"/api/v1/tasks/{task_id}/comments", headers=member_headers)
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1
    assert r_list.json()[0]["content"] == "I am working on this task now."
