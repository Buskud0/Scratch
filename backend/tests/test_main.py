# to run the tests:
# > pytest

import os

adminCode = os.getenv("ADMIN_CODE")

# --- HELPER FUNCTIONS ---

def register_user(client, username="testuser", password="password123", admin_code=None):
    payload = {"username": username, "password": password}
    if admin_code:
        payload["admin"] = admin_code
    return client.post("/users/register", json=payload)

def login_user(client, username="testuser", password="password123"):
    response = client.post("/users/login", json={"username": username, "password": password})
    return response.json().get("token")

def get_auth_headers(client, username="testuser", password="password123", admin_code=None):
    register_user(client, username, password, admin_code)
    token = login_user(client, username, password)
    return {"Authorization": f"Bearer {token}"}

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

# GET ALL TASKS
def test_get_tasks_success_and_contract(client):
    user = get_auth_headers(client, "user1", "pass1")
    create_task(client, user, title="Task 1")
    
    response = client.get("/tasks", headers=user)
    assert response.status_code == 200
    
    task_schema = {"id": int, "title": str, "done": bool, "owner_id": int}
    validate_schema(response.json()[0], task_schema)

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

