# to run the tests:
# > pytest

import os

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Woohoo!"}

def test_register_user(client):
    payload = {
        "username": "testuser",
        "password": "testpassword123"
    }
    response = client.post("/users/register", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User created successfully!"
    assert "id" in data

def test_register_duplicate_user(client):
    payload = {
        "username": "sameuser",
        "password": "password"
    }
    client.post("/users/register", json=payload)
    response = client.post("/users/register", json=payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "User by this name already exists"

def test_register_admin(client):
    admin_pw = os.getenv("ADMIN_CODE") 
    
    payload = {
        "username": "adminuser",
        "password": "adminpassword",
        "admin": admin_pw
    }
    response = client.post("/users/register", json=payload)
    
    assert response.status_code == 200
    if "admin" in response.json():
        assert response.json()["admin"] is True

def test_login_success(client):
    client.post("/users/register", json={"username": "loginuser", "password": "password123"})
    
    response = client.post("/users/login", json={"username": "loginuser", "password": "password123"})
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert isinstance(data["token"], str)

def test_login_wrong_password(client):
    client.post("/users/register", json={"username": "wrongpassuser", "password": "correctpassword"})
    
    response = client.post("/users/login", json={"username": "wrongpassuser", "password": "WRONGpassword"})
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_login_nonexistent_user(client):
    response = client.post("/users/login", json={"username": "nobody", "password": "password"})
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Wrong credentials"

def test_create_task(client):
    client.post("/users/register", json={"username": "taskuser", "password": "password"})
    login_res = client.post("/users/login", json={"username": "taskuser", "password": "password"})
    token = login_res.json()["token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": "Mano pirma užduotis"}
    
    response = client.post("/tasks", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Mano pirma užduotis"
    assert data["done"] is False
    assert "id" in data

def test_get_tasks(client):
    client.post("/users/register", json={"username": "getuser", "password": "password"})
    token = client.post("/users/login", json={"username": "getuser", "password": "password"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    client.post("/tasks", json={"title": "Task 1"}, headers=headers)
    client.post("/tasks", json={"title": "Task 2"}, headers=headers)
    
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_tasks_unauthorized(client):
    response = client.get("/tasks")
    assert response.status_code == 401

def test_task_privacy(client):
    client.post("/users/register", json={"username": "userA", "password": "password"})
    tokenA = client.post("/users/login", json={"username": "userA", "password": "password"}).json()["token"]
    res = client.post("/tasks", json={"title": "A slaptas planas"}, headers={"Authorization": f"Bearer {tokenA}"})
    taskA_id = res.json()["id"]

    client.post("/users/register", json={"username": "userB", "password": "password"})
    tokenB = client.post("/users/login", json={"username": "userB", "password": "password"}).json()["token"]

    response = client.get(f"/tasks/{taskA_id}", headers={"Authorization": f"Bearer {tokenB}"})
    
    assert response.status_code == 404

def test_update_task(client):
    client.post("/users/register", json={"username": "upuser", "password": "password"})
    token = client.post("/users/login", json={"username": "upuser", "password": "password"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    task_res = client.post("/tasks", json={"title": "Pradinis"}, headers=headers)
    task_id = task_res.json()["id"]

    update_payload = {"title": "Pakeistas", "done": True}
    response = client.patch(f"/tasks/{task_id}", json=update_payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["title"] == "Pakeistas"
    assert response.json()["done"] is True

def test_delete_task(client):
    client.post("/users/register", json={"username": "deluser", "password": "password"})
    token = client.post("/users/login", json={"username": "deluser", "password": "password"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    task_res = client.post("/tasks", json={"title": "Ištrinti mane"}, headers=headers)
    task_id = task_res.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    
    check_res = client.get(f"/tasks/{task_id}", headers=headers)
    assert check_res.status_code == 404

def test_admin_get_all_users(client):
    admin_code = os.getenv("ADMIN_CODE") 
    client.post("/users/register", json={
        "username": "superadmin", 
        "password": "password", 
        "admin": admin_code
    })
    
    login_res = client.post("/users/login", json={"username": "superadmin", "password": "password"})
    token = login_res.json()["token"]
    
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_user_cannot_get_all_users(client):
    client.post("/users/register", json={"username": "regular", "password": "password"})
    token = client.post("/users/login", json={"username": "regular", "password": "password"}).json()["token"]
    
    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Missing administator permissions"

def test_admin_delete_other_user(client):
    res = client.post("/users/register", json={"username": "victim", "password": "password"})
    victim_id = res.json()["id"]
    
    admin_code = os.getenv("ADMIN_CODE", "tavo_slaptas_kodas") 
    client.post("/users/register", json={"username": "boss", "password": "password", "admin": admin_code})
    admin_token = client.post("/users/login", json={"username": "boss", "password": "password"}).json()["token"]
    
    response = client.delete(f"/users/{victim_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200