# to run the tests:
# > pytest

import os

from dotenv import load_dotenv

from app.models import Task, User
from app.schemas import (
    DeleteUserResponse,
    LoginResponse,
    RegisterResponse,
    TaskResponse,
    UserResponse,
)

load_dotenv()
adminCode = os.getenv("ADMIN_CODE")

# --- HELPER FUNCTIONS ---


def register_user(client, username="testuser", password="password123", admin_code=None):
    payload = {"username": username, "password": password, "admin_code": admin_code}
    return client.post("/users/register", json=payload)


def login_user(client, username="testuser", password="password123"):
    response = client.post("/users/login", json={"username": username, "password": password})
    return response.json().get("token")


def get_auth_headers(client, username="testuser", password="password123", admin_code=None):
    reg_response = register_user(client, username, password, admin_code)
    token = login_user(client, username, password)
    user_id = reg_response.json().get("id")
    return {"Authorization": f"Bearer {token}", "id": str(user_id)}


def get_admin_headers(client, username="admin", password="password123"):
    return get_auth_headers(client, username, password, admin_code=adminCode)


def create_task(client, headers, title="Test Task", done=False):
    return client.post("/tasks", json={"title": title, "done": done}, headers=headers)


# --- TESTS ---

# get all tasks
def test_get_tasks_success_and_contract(client):
    user = get_auth_headers(client, "user1", "pass1")
    create_task(client, user, title="Task 1")

    response = client.get("/tasks", headers=user)
    assert response.status_code == 200
    TaskResponse.model_validate(response.json()[0])


def test_get_tasks_filtering(client):
    user = get_auth_headers(client, "filter_user", "pass")
    create_task(client, user, title="Done", done=True)
    create_task(client, user, title="Not Done", done=False)

    response = client.get("/tasks?done=true", headers=user)
    assert len(response.json()) == 1
    assert response.json()[0]["done"] is True


def test_get_tasks_privacy(client):
    user1 = get_auth_headers(client, "userA", "pass")
    user2 = get_auth_headers(client, "userB", "pass")

    create_task(client, user1, title="User A Task")

    response = client.get("/tasks", headers=user2)
    assert response.json() == []


def test_get_tasks_unauthorized(client):
    response = client.get("/tasks")
    assert response.status_code == 401


# get a singular task
def test_get_task_success_and_contract(client):
    user = get_auth_headers(client, "single_task_user", "pass")
    created_res = create_task(client, user, title="Specific Task")
    task_id = created_res.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=user)
    assert response.status_code == 200
    TaskResponse.model_validate(response.json())
    assert response.json()["title"] == "Specific Task"


def test_get_task_privacy(client):
    user1 = get_auth_headers(client, "owner", "pass")
    user2 = get_auth_headers(client, "hacker", "pass")

    created_res = create_task(client, user1, title="Owner's Private Task")
    task_id = created_res.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=user2)
    assert response.status_code == 404


def test_get_task_not_found(client):
    user = get_auth_headers(client, "lookup_user", "pass")

    response = client.get("/tasks/99999", headers=user)

    assert response.status_code == 404


def test_get_task_unauthorized(client):
    response = client.get("/tasks/1")
    assert response.status_code == 401


# add a new task
def test_add_task_success_and_contract(client):
    username, password = "creator_user", "password123"
    headers = get_auth_headers(client, username, password)

    user_id = int(headers.get("id"))

    payload = {"title": "Clean the kitchen"}
    response = client.post("/tasks", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()

    TaskResponse.model_validate(data)

    assert data["title"] == "Clean the kitchen"
    assert data["owner_id"] == user_id


def test_add_task_title_too_long(client):
    headers = get_auth_headers(client, "long_title_user", "pass")
    response = client.post("/tasks", json={"title": "x" * 51}, headers=headers)
    assert response.status_code == 422


def test_add_task_empty_title(client):
    headers = get_auth_headers(client, "empty_title_user", "pass")
    response = client.post("/tasks", json={"title": ""}, headers=headers)
    assert response.status_code == 422


def test_add_task_unauthorized(client):
    response = client.post("/tasks", json={"title": "Should fail"})
    assert response.status_code == 401


def test_add_task_invalid_data(client):
    headers = get_auth_headers(client, "valid_user", "pass")

    response = client.post("/tasks", json={}, headers=headers)
    assert response.status_code == 422


# update a task
def test_update_task_success_and_contract(client):
    headers = get_auth_headers(client, "updater", "pass")
    task_res = create_task(client, headers, title="Old Title", done=False)
    task_id = task_res.json()["id"]

    payload = {"title": "New Title", "done": True}
    response = client.patch(f"/tasks/{task_id}", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    TaskResponse.model_validate(data)
    assert data["title"] == "New Title"
    assert data["done"] is True


def test_update_task_privacy(client):
    headers_owner = get_auth_headers(client, "owner", "pass")
    headers_hacker = get_auth_headers(client, "hacker", "pass")

    task_res = create_task(client, headers_owner, title="Private")
    task_id = task_res.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_hacker)
    assert response.status_code == 404


def test_update_task_not_found(client):
    headers = get_auth_headers(client, "user", "pass")
    response = client.patch("/tasks/9999", json={"title": "Doesn't exist"}, headers=headers)
    assert response.status_code == 404


def test_update_task_unauthorized(client):
    response = client.patch("/tasks/1", json={"title": "Fail"})
    assert response.status_code == 401


# delete all tasks
def test_delete_all_tasks_success(client, session):
    headers = get_auth_headers(client, "cleaner", "pass")
    create_task(client, headers, title="Task 1")
    create_task(client, headers, title="Task 2")

    response = client.delete("/tasks", headers=headers)

    assert response.status_code == 204

    db_count = session.query(Task).count()
    assert db_count == 0


def test_delete_all_tasks_privacy(client, session):
    headers_a = get_auth_headers(client, "user_a", "pass")
    headers_b = get_auth_headers(client, "user_b", "pass")

    create_task(client, headers_a, title="A's task")
    create_task(client, headers_b, title="B's task")

    client.delete("/tasks", headers=headers_a)

    db_tasks_b = session.query(Task).all()
    assert len(db_tasks_b) == 1
    assert db_tasks_b[0].title == "B's task"


def test_delete_all_tasks_no_tasks(client):
    headers = get_auth_headers(client, "empty_user", "pass")
    response = client.delete("/tasks", headers=headers)
    assert response.status_code == 204


def test_delete_all_tasks_unauthorized(client):
    response = client.delete("/tasks")
    assert response.status_code == 401


# delete a task
def test_delete_task_success(client, session):
    headers = get_auth_headers(client, "delete_user", "pass123")
    task_res = create_task(client, headers, title="Task to Delete")
    task_id = task_res.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers)

    assert response.status_code == 200

    db_task = session.query(Task).filter(Task.id == task_id).first()
    assert db_task is None


def test_delete_task_privacy(client, session):
    headers_owner = get_auth_headers(client, "owner", "pass")
    headers_hacker = get_auth_headers(client, "hacker", "pass")

    task_res = create_task(client, headers_owner, title="Private Task")
    task_id = task_res.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers_hacker)

    assert response.status_code == 404

    db_task = session.query(Task).filter(Task.id == task_id).first()
    assert db_task is not None


def test_delete_task_not_found(client):
    headers = get_auth_headers(client, "user", "pass")
    response = client.delete("/tasks/99999", headers=headers)

    assert response.status_code == 404


def test_delete_task_unauthorized(client):
    response = client.delete("/tasks/1")
    assert response.status_code == 401


# get all users
def test_get_all_users_admin_success_and_contract(client):
    admin_headers = get_admin_headers(client, "admin_boss")

    register_user(client, "other_user", "pass")

    response = client.get("/users", headers=admin_headers)

    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2

    for user in users:
        UserResponse.model_validate(user)
        assert "password" not in user


def test_get_all_users_regular_user_forbidden(client):
    regular_headers = get_auth_headers(client, "regular_joe", "pass")

    response = client.get("/users", headers=regular_headers)

    assert response.status_code == 403


def test_get_all_users_unauthorized(client):
    response = client.get("/users")
    assert response.status_code == 401


# get a singular user
def test_get_user_admin_success_and_contract(client):
    admin_headers = get_admin_headers(client, "admin_user")

    res = register_user(client, "target_user", "pass")
    target_id = res.json()["id"]

    response = client.get(f"/users/{target_id}", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()

    UserResponse.model_validate(data)
    assert data["username"] == "target_user"
    assert "password" not in data


def test_get_user_self_success(client):
    headers = get_auth_headers(client, "fresh_user", "pass123")
    uid = int(headers.get("id"))

    response = client.get(f"/users/{uid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "fresh_user"


def test_get_user_privacy_forbidden(client):
    user_a_headers = get_auth_headers(client, "user_a", "pass")
    user_b_headers = get_auth_headers(client, "user_b", "pass")
    user_b_id = int(user_b_headers.get("id"))

    response = client.get(f"/users/{user_b_id}", headers=user_a_headers)

    assert response.status_code == 403


def test_get_user_not_found(client):
    admin_headers = get_admin_headers(client, "admin_searcher")

    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404


def test_get_user_unauthorized(client):
    response = client.get("/users/1")
    assert response.status_code == 401


# register a new user
def test_register_long_password(client):
    long_password = "a" * 100
    payload = {"username": "long_pass_user", "password": long_password}

    response = client.post("/users/register", json=payload)

    assert response.status_code == 201


def test_register_user_success_and_contract(client, session):
    payload = {
        "username": "new_regular_user",
        "password": "securepassword123",
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    RegisterResponse.model_validate(data)

    db_user = session.query(User).filter(User.id == data["id"]).first()
    assert db_user is not None
    assert db_user.is_admin is False
    assert db_user.username == "new_regular_user"
    assert db_user.password != "securepassword123"


def test_register_admin_success(client):
    payload = {
        "username": "new_admin",
        "password": "adminpassword",
        "admin_code": adminCode,
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 201
    assert response.json()["is_admin"] is True


def test_register_admin_incorrect_code(client):
    payload = {
        "username": "hacker_admin",
        "password": "password",
        "admin_code": "wrong_secret_code",
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 401


def test_register_duplicate_username(client):
    payload = {"username": "duplicate", "password": "password"}
    client.post("/users/register", json=payload)

    response = client.post("/users/register", json=payload)

    assert response.status_code == 400


def test_register_invalid_data(client):
    response = client.post("/users/register", json={"username": "missing_password"})
    assert response.status_code == 422


def test_register_username_too_long(client):
    response = client.post("/users/register", json={"username": "x" * 21, "password": "pass"})
    assert response.status_code == 422


# login a user
def test_login_success_and_contract(client):
    username, password = "login_test_user", "password123"
    register_user(client, username, password)

    payload = {"username": username, "password": password}
    response = client.post("/users/login", json=payload)

    assert response.status_code == 200
    data = response.json()

    LoginResponse.model_validate(data)

    assert data["is_admin"] is False
    assert len(data["token"]) > 20


def test_login_wrong_password(client):
    username, password = "secure_user", "real_password"
    register_user(client, username, password)

    payload = {"username": username, "password": "wrong_password"}
    response = client.post("/users/login", json=payload)

    assert response.status_code == 401


def test_login_user_not_found(client):
    payload = {"username": "ghost_user", "password": "some_password"}
    response = client.post("/users/login", json=payload)

    assert response.status_code == 400


def test_login_missing_fields(client):
    response = client.post("/users/login", json={"username": "only_name"})
    assert response.status_code == 422


# delete a user
def test_delete_user_self_success(client, session):
    username, password = "bye_user", "pass123"

    headers = get_auth_headers(client, username, password)
    user_id = int(headers.get("id"))

    response = client.delete(f"/users/{user_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()

    DeleteUserResponse.model_validate(data)
    assert data["username"] == username

    db_user = session.query(User).filter(User.id == user_id).first()
    assert db_user is None


def test_delete_user_admin_success(client, session):
    admin_headers = get_admin_headers(client, "boss_man")

    victim_res = register_user(client, "victim_user", "password")
    victim_id = victim_res.json()["id"]

    response = client.delete(f"/users/{victim_id}", headers=admin_headers)

    assert response.status_code == 200

    db_user = session.query(User).filter(User.id == victim_id).first()
    assert db_user is None


def test_delete_user_with_tasks_cascades(client, session):
    username, password = "working_user", "pass"
    headers = get_auth_headers(client, username, password)
    user_id = int(headers.get("id"))
    create_task(client, headers, title="Task 1")
    create_task(client, headers, title="Task 2")

    response = client.delete(f"/users/{user_id}", headers=headers)

    assert response.status_code == 200
    assert session.query(User).filter(User.id == user_id).first() is None
    assert session.query(Task).filter(Task.owner_id == user_id).count() == 0


def test_delete_user_privacy_forbidden(client, session):
    headers_a = get_auth_headers(client, "user_a", "pass")

    res_b = register_user(client, "user_b", "pass")
    user_b_id = res_b.json()["id"]

    response = client.delete(f"/users/{user_b_id}", headers=headers_a)

    assert response.status_code == 403

    db_user_b = session.query(User).filter(User.id == user_b_id).first()
    assert db_user_b is not None


def test_delete_user_not_found(client):
    admin_headers = get_admin_headers(client, "admin_cleaner")

    response = client.delete("/users/99999", headers=admin_headers)
    assert response.status_code == 404


def test_delete_user_unauthorized(client):
    response = client.delete("/users/1")
    assert response.status_code == 401


# update user
def test_update_user_self_success(client):
    auth = get_auth_headers(client, "oldname", "pass123")
    user_id = auth.get("id")

    payload = {"username": "newname"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    data = response.json()

    UserResponse.model_validate(data)
    assert data["username"] == "newname"


def test_update_user_password_hashing(client, session):
    auth = get_auth_headers(client, "hashuser", "oldpass")
    user_id = int(auth.get("id"))

    payload = {"password": "new_secure_password"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200

    db_user = session.query(User).filter(User.id == user_id).first()
    assert db_user.password != "new_secure_password"
    assert len(db_user.password) > 30


def test_update_user_privacy_forbidden(client):
    auth_a = get_auth_headers(client, "user_a", "pass")
    auth_b = get_auth_headers(client, "user_b", "pass")
    user_b_id = auth_b.get("id")

    response = client.patch(f"/users/{user_b_id}", json={"username": "hacked"}, headers=auth_a)

    assert response.status_code == 403


def test_update_user_not_found_by_regular_user(client):
    auth = get_auth_headers(client, "regular_user", "pass")

    response = client.patch("/users/99999", json={"username": "ghost"}, headers=auth)
    assert response.status_code == 404


def test_update_user_promote_to_admin(client):
    auth = get_auth_headers(client, "regular_user", "pass")
    user_id = auth.get("id")

    payload = {"admin_code": adminCode}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    assert response.json()["is_admin"] is True


def test_update_user_demote_admin(client):
    auth = get_auth_headers(client, "admin_to_demote", "pass", admin_code=adminCode)
    user_id = auth.get("id")

    payload = {"admin_code": "false"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    assert response.json()["is_admin"] is False


def test_update_user_wrong_admin_code(client):
    auth = get_auth_headers(client, "user", "pass")
    user_id = auth.get("id")

    payload = {"admin_code": "wrong_code_123"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 401


def test_update_user_not_found(client):
    admin_headers = get_admin_headers(client, "admin")

    response = client.patch("/users/99999", json={"username": "ghost"}, headers=admin_headers)
    assert response.status_code == 404


def test_update_user_unauthorized(client):
    response = client.patch("/users/1", json={"username": "anon"})
    assert response.status_code == 401