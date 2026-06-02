# to run the tests:
# > pytest

import os
from dotenv import load_dotenv
from schemas import TaskResponse, UserResponse, RegisterResponse, LoginResponse, DeleteUserResponse

load_dotenv()
adminCode = os.getenv("ADMIN_CODE")

# --- HELPER FUNCTIONS ---

def register_user(client, username="testuser", password="password123", admin_code=None):
    payload = {"username": username, "password": password, 
               "admin_code": admin_code}
    return client.post("/users/register", json=payload)

def login_user(client, username="testuser", password="password123"):
    response = client.post("/users/login", json={"username": username, "password": password})
    return response.json().get("token")

def get_auth_headers(client, username="testuser", password="password123", admin_code=None):
    regResponse = register_user(client, username, password, admin_code)
    token = login_user(client, username, password)
    id = regResponse.json().get("id")
    return {"Authorization": f"Bearer {token}", "id":str(id)}

def create_task(client, headers, title="Test Task", done=False):
    return client.post("/tasks", json={"title": title, "done": done}, headers=headers)

def validate_schema(data, schema):
    """
    Patikrina, ar žodynas (data) turi visus laukus ir ar jų tipai teisingi.
    schema = {"laukas": tipas, "kitas_laukas": kitas_tipas}
    """
    for field, expected_type in schema.items():
        assert field in data, f"Missing field: '{field}' in response"
        assert isinstance(data[field], expected_type), \
            f"Field '{field}' should be {expected_type}, but got {type(data[field])}"

# --- TESTS ---

# get all tasks
def test_get_tasks_success_and_contract(client):
    """
    Verify successful retrieval of task list and schema compliance.
    """
    user = get_auth_headers(client, "user1", "pass1")
    create_task(client, user, title="Task 1")
    
    response = client.get("/tasks", headers=user)
    assert response.status_code == 200
    TaskResponse.model_validate(response.json()[0])

def test_get_tasks_filtering(client):
    """
    Verify that the 'done' query parameter correctly filters tasks.
    """
    user = get_auth_headers(client, "filter_user", "pass")
    create_task(client, user, title="Done", done=True)
    create_task(client, user, title="Not Done", done=False)

    response = client.get("/tasks?done=true", headers=user)
    assert len(response.json()) == 1
    assert response.json()[0]["done"] is True

def test_get_tasks_privacy(client):
    """
    Verify that a user cannot see another user's tasks.
    """
    user1 = get_auth_headers(client, "userA", "pass")
    user2 = get_auth_headers(client, "userB", "pass")
    
    create_task(client, user1, title="User A Task")

    response = client.get("/tasks", headers=user2)
    assert response.json() == []

def test_get_tasks_unauthorized(client):
    """
    Verify that access is blocked without a valid JWT token.
    """
    response = client.get("/tasks")
    assert response.status_code == 401

# get a singular task
def test_get_task_success_and_contract(client):
    """Test successfully getting a task by ID and verifying the schema."""
    user = get_auth_headers(client, "single_task_user", "pass")
    created_res = create_task(client, user, title="Specific Task")
    task_id = created_res.json()["id"]
    
    response = client.get(f"/tasks/{task_id}", headers=user)
    assert response.status_code == 200
    TaskResponse.model_validate(response.json())
    assert response.json()["title"] == "Specific Task"

def test_get_task_privacy(client):
    """Test that a user cannot see someone else's task by ID (Should return 404)."""
    user1 = get_auth_headers(client, "owner", "pass")
    user2 = get_auth_headers(client, "hacker", "pass")
    
    created_res = create_task(client, user1, title="Owner's Private Task")
    task_id = created_res.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=user2)
    assert response.status_code == 404

def test_get_task_not_found(client):
    """Test requesting an ID that simply doesn't exist in the database."""
    user = get_auth_headers(client, "lookup_user", "pass")
    
    response = client.get("/tasks/99999", headers=user)
    
    assert response.status_code == 404

def test_get_task_unauthorized(client):
    """Test that requesting a task without a token returns 401."""
    response = client.get("/tasks/1")
    assert response.status_code == 401

# add a new task
def test_add_task_success_and_contract(client):
    """
    Test successful task creation, ownership assignment, 
    and database persistence.
    """
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

def test_add_task_unauthorized(client):
    """
    Verify that task creation is blocked for unauthenticated users.
    """
    response = client.post("/tasks", json={"title": "Should fail"})
    assert response.status_code == 401

def test_add_task_invalid_data(client):
    """
    Verify that Pydantic validation catches missing required fields.
    """
    headers = get_auth_headers(client, "valid_user", "pass")
    
    response = client.post("/tasks", json={}, headers=headers)
    assert response.status_code == 422

# update a task
def test_update_task_success_and_contract(client, session):
    """
    Test successful partial update of a task.
    """
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
    """
    Verify that a user cannot update a task belonging to another user.
    """
    headers_owner = get_auth_headers(client, "owner", "pass")
    headers_hacker = get_auth_headers(client, "hacker", "pass")
    
    task_res = create_task(client, headers_owner, title="Private")
    task_id = task_res.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Hacked"}, headers=headers_hacker)
    assert response.status_code == 404

def test_update_task_not_found(client):
    """
    Verify 404 response when attempting to update a non-existent task ID.
    """
    headers = get_auth_headers(client, "user", "pass")
    response = client.patch("/tasks/9999", json={"title": "Doesn't exist"}, headers=headers)
    assert response.status_code == 404

def test_update_task_unauthorized(client):
    """
    Verify that updates are blocked without a valid JWT token.
    """
    response = client.patch("/tasks/1", json={"title": "Fail"})
    assert response.status_code == 401

# delete all tasks
def test_delete_all_tasks_success(client, session):
    """
    Verify that a user can delete all of their own tasks and 
    ensure they are removed from the database.
    """
    from models import Task
    headers = get_auth_headers(client, "cleaner", "pass")
    create_task(client, headers, title="Task 1")
    create_task(client, headers, title="Task 2")

    response = client.delete("/tasks", headers=headers)
    
    assert response.status_code == 200
    
    db_count = session.query(Task).count()
    assert db_count == 0

def test_delete_all_tasks_privacy(client, session):
    """
    Verify that deleting all tasks only affects the authenticated user's tasks.
    """
    from models import Task
    headers_a = get_auth_headers(client, "user_a", "pass")
    headers_b = get_auth_headers(client, "user_b", "pass")
    
    create_task(client, headers_a, title="A's task")
    create_task(client, headers_b, title="B's task")

    client.delete("/tasks", headers=headers_a)
    
    db_tasks_b = session.query(Task).all()
    assert len(db_tasks_b) == 1
    assert db_tasks_b[0].title == "B's task"

def test_delete_all_tasks_not_found(client):
    """
    Verify 404 response when a user attempts to delete all tasks but has none.
    """
    headers = get_auth_headers(client, "empty_user", "pass")
    response = client.delete("/tasks", headers=headers)
    assert response.status_code == 404

def test_delete_all_tasks_unauthorized(client):
    """
    Verify that the delete all operation is blocked without a valid JWT token.
    """
    response = client.delete("/tasks")
    assert response.status_code == 401

# delete a task
def test_delete_task_success(client, session):
    """
    Verify that a user can delete their own task and it is removed from the database.
    """
    from models import Task
    headers = get_auth_headers(client, "delete_user", "pass123")
    task_res = create_task(client, headers, title="Task to Delete")
    task_id = task_res.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers)
    
    assert response.status_code == 200

    db_task = session.query(Task).filter(Task.id == task_id).first()
    assert db_task is None

def test_delete_task_privacy(client, session):
    """
    Verify that a user cannot delete a task belonging to another user.
    """
    from models import Task
    headers_owner = get_auth_headers(client, "owner", "pass")
    headers_hacker = get_auth_headers(client, "hacker", "pass")

    task_res = create_task(client, headers_owner, title="Private Task")
    task_id = task_res.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers_hacker)
    
    assert response.status_code == 404

    db_task = session.query(Task).filter(Task.id == task_id).first()
    assert db_task is not None

def test_delete_task_not_found(client):
    """
    Verify 404 response when attempting to delete a non-existent task ID.
    """
    headers = get_auth_headers(client, "user", "pass")
    response = client.delete("/tasks/99999", headers=headers)
    
    assert response.status_code == 404

def test_delete_task_unauthorized(client):
    """
    Verify that task deletion is blocked without a valid JWT token.
    """
    response = client.delete("/tasks/1")
    assert response.status_code == 401

# get all users
def test_get_all_users_admin_success_and_contract(client):
    """
    Verify that an admin can retrieve the full user list and that 
    the response follows the UserResponse schema (no passwords).
    """
    admin_headers = get_auth_headers(client, "admin_boss", "pass", admin_code=adminCode)
    
    register_user(client, "other_user", "pass")

    response = client.get("/users", headers=admin_headers)
    
    assert response.status_code == 200
    users = response.json()
    assert len(users) == 2

    for user in users:
        UserResponse.model_validate(user)
        assert "password" not in user

def test_get_all_users_regular_user_forbidden(client):
    """
    Verify that a non-admin user receives a 403 Forbidden error 
    when attempting to list all users.
    """
    regular_headers = get_auth_headers(client, "regular_joe", "pass")
    
    response = client.get("/users", headers=regular_headers)
    
    assert response.status_code == 403

def test_get_all_users_unauthorized(client):
    """
    Verify that the user list is protected and returns 401 for 
    unauthenticated requests.
    """
    response = client.get("/users")
    assert response.status_code == 401

# get a singular user
def test_get_user_admin_success_and_contract(client):
    """
    Verify that an admin can retrieve another user's details 
    and that the response follows the UserResponse schema.
    """
    admin_headers = get_auth_headers(client, "admin_user", "pass", admin_code=adminCode)
    
    res = register_user(client, "target_user", "pass")
    target_id = res.json()["id"]

    response = client.get(f"/users/{target_id}", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    UserResponse.model_validate(data)
    assert data["username"] == "target_user"
    assert "password" not in data

def test_get_user_self_success(client):
    """
    Verify that a regular user can retrieve their own details.
    """
    headers = get_auth_headers(client, "fresh_user", "pass123")
    uid = int(headers.get("id"))

    response = client.get(f"/users/{uid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == "fresh_user"

def test_get_user_privacy_forbidden(client):
    """
    Verify that a regular user receives 403 when trying to access 
    another user's details.
    """
    user_a_headers = get_auth_headers(client, "user_a", "pass")
    user_b_headers = get_auth_headers(client, "user_b", "pass")
    user_b_id = int(user_b_headers.get("id"))

    response = client.get(f"/users/{user_b_id}", headers=user_a_headers)
    
    assert response.status_code == 403

def test_get_user_not_found(client):
    """
    Verify 404 response when an admin searches for a non-existent user ID.
    """
    admin_headers = get_auth_headers(client, "admin_searcher", "pass", admin_code=adminCode)
    
    response = client.get("/users/99999", headers=admin_headers)
    assert response.status_code == 404

def test_get_user_unauthorized(client):
    """
    Verify that user detail access is blocked without a valid JWT token.
    """
    response = client.get("/users/1")
    assert response.status_code == 401

# register a new user
def test_register_enormous_password(client):
    """Verify the system handles or truncates passwords over 72 bytes."""
    long_password = "a" * 100 # Over the 72 limit
    payload = {"username": "long_pass_user", "password": long_password}
    
    response = client.post("/users/register", json=payload)
    
    assert response.status_code != 500

def test_register_user_success_and_contract(client, session):
    """
    Verify that a regular user can register successfully, the response 
    matches the contract, and the password is correctly hashed in the DB.
    """
    from models import User
    payload = {
        "username": "new_regular_user",
        "password": "securepassword123"
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
    """
    Verify that providing the correct admin code grants admin privileges.
    """
    payload = {
        "username": "new_admin",
        "password": "adminpassword",
        "admin_code": adminCode
    }
    
    response = client.post("/users/register", json=payload)
    
    assert response.status_code == 201
    assert response.json()["is_admin"] is True

def test_register_admin_incorrect_code(client):
    """
    Verify that an incorrect admin code returns a 401 Unauthorized error.
    """
    payload = {
        "username": "hacker_admin",
        "password": "password",
        "admin_code": "wrong_secret_code"
    }
    
    response = client.post("/users/register", json=payload)
    
    assert response.status_code == 401

def test_register_duplicate_username(client):
    """
    Verify that registering a username that already exists returns a 400 error.
    """
    payload = {"username": "duplicate", "password": "password"}
    client.post("/users/register", json=payload)
    
    response = client.post("/users/register", json=payload)
    
    assert response.status_code == 400

def test_register_invalid_data(client):
    """
    Verify that Pydantic validation handles missing required fields.
    """
    response = client.post("/users/register", json={"username": "missing_password"})
    assert response.status_code == 422

# login a user
def test_login_success_and_contract(client):
    """
    Verify that a registered user can log in and receives a valid token 
    along with the correct user metadata and status code.
    """
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
    """
    Verify that login fails with a 401 error when the password is incorrect.
    """
    username, password = "secure_user", "real_password"
    register_user(client, username, password)
    
    payload = {"username": username, "password": "wrong_password"}
    response = client.post("/users/login", json=payload)
    
    assert response.status_code == 401

def test_login_user_not_found(client):
    """
    Verify that login fails with a 400 error when the username does not exist.
    """
    payload = {"username": "ghost_user", "password": "some_password"}
    response = client.post("/users/login", json=payload)
    
    assert response.status_code == 400

def test_login_missing_fields(client):
    """
    Verify that the API returns a 422 error for incomplete login payloads.
    """
    response = client.post("/users/login", json={"username": "only_name"})
    assert response.status_code == 422

# delete a user
def test_delete_user_self_success(client, session):
    """
    Verify that a regular user can delete their own account and 
    ensure it is removed from the database.
    """
    from models import User
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
    """
    Verify that an admin can delete another user's account.
    """
    from models import User
    
    admin_headers = get_auth_headers(client, "boss_man", "pass", admin_code=adminCode)
    
    victim_res = register_user(client, "victim_user", "password")
    victim_id = victim_res.json()["id"]

    response = client.delete(f"/users/{victim_id}", headers=admin_headers)
    
    assert response.status_code == 200
    
    db_user = session.query(User).filter(User.id == victim_id).first()
    assert db_user is None

def test_delete_user_privacy_forbidden(client, session):
    """
    Verify that a regular user receives a 403 Forbidden error when 
    attempting to delete someone else's account.
    """
    from models import User
    
    headers_a = get_auth_headers(client, "user_a", "pass")
    
    res_b = register_user(client, "user_b", "pass")
    user_b_id = res_b.json()["id"]

    response = client.delete(f"/users/{user_b_id}", headers=headers_a)
    
    assert response.status_code == 403

    db_user_b = session.query(User).filter(User.id == user_b_id).first()
    assert db_user_b is not None

def test_delete_user_not_found(client):
    """
    Verify 404 response when attempting to delete a non-existent user ID.
    """
    admin_headers = get_auth_headers(client, "admin_cleaner", "pass", admin_code=adminCode)
    
    response = client.delete("/users/99999", headers=admin_headers)
    assert response.status_code == 404

def test_delete_user_unauthorized(client):
    """
    Verify that user deletion is blocked without a valid JWT token.
    """
    response = client.delete("/users/1")
    assert response.status_code == 401

# update user
def test_update_user_self_success(client):
    """
    Verify that a user can update their own username and the response matches the schema.
    """
    auth = get_auth_headers(client, "oldname", "pass123")
    user_id = auth.get("id")

    payload = {"username": "newname"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    data = response.json()
    
    UserResponse.model_validate(data)
    assert data["username"] == "newname"

def test_update_user_password_hashing(client, session):
    """
    Verify that updating a password correctly hashes the new password in the database.
    """
    from models import User
    auth = get_auth_headers(client, "hashuser", "oldpass")
    user_id = int(auth.get("id"))

    payload = {"password": "new_secure_password"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    
    db_user = session.query(User).filter(User.id == user_id).first()
    assert db_user.password != "new_secure_password"
    assert len(db_user.password) > 30 # Check it's a hash string

def test_update_user_privacy_forbidden(client):
    """
    Verify that User A cannot update User B's details (403).
    """
    auth_a = get_auth_headers(client, "user_a", "pass")
    auth_b = get_auth_headers(client, "user_b", "pass")
    user_b_id = auth_b.get("id")

    response = client.patch(f"/users/{user_b_id}", json={"username": "hacked"}, headers=auth_a)
    
    assert response.status_code == 403

def test_update_user_promote_to_admin(client):
    """
    Verify that a user becomes an admin when providing the correct admin_code.
    """
    auth = get_auth_headers(client, "regular_user", "pass")
    user_id = auth.get("id")

    payload = {"admin_code": adminCode}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    assert response.json()["is_admin"] is True

def test_update_user_demote_admin(client):
    """
    Verify that an admin can be demoted by providing "false" as the admin_code.
    """
    auth = get_auth_headers(client, "admin_to_demote", "pass", admin_code=adminCode)
    user_id = auth.get("id")

    payload = {"admin_code": "false"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 200
    assert response.json()["is_admin"] is False

def test_update_user_wrong_admin_code(client):
    """
    Verify that an incorrect admin code returns a 401 Unauthorized error.
    """
    auth = get_auth_headers(client, "user", "pass")
    user_id = auth.get("id")

    payload = {"admin_code": "wrong_code_123"}
    response = client.patch(f"/users/{user_id}", json=payload, headers=auth)

    assert response.status_code == 401

def test_update_user_not_found(client):
    """
    Verify that an admin trying to update a non-existent ID gets a 404.
    """
    admin_headers = get_auth_headers(client, "admin", "pass", admin_code=adminCode)
    
    response = client.patch("/users/99999", json={"username": "ghost"}, headers=admin_headers)
    assert response.status_code == 404

def test_update_user_unauthorized(client):
    """
    Verify that the endpoint is protected by JWT.
    """
    response = client.patch("/users/1", json={"username": "anon"})
    assert response.status_code == 401