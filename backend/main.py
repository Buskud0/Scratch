# Scratch TO-DO app!
# > fastapi dev - run the app

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from passlib.hash import pbkdf2_sha256
from typing import List
import models
import schemas
import jwt
import os
from datetime import datetime, timezone, timedelta
from fastapi.security import OAuth2PasswordBearer

Base.metadata.create_all(bind=engine)
app = FastAPI()
secretKey = os.getenv("SECRET_KEY")
adminCode = os.getenv("ADMIN_CODE")
getToken = OAuth2PasswordBearer(tokenUrl="login")

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def createToken(id: int):
    payload = {
        "sub": str(id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, secretKey, algorithm="HS256")
    return token

def verifyToken(token: str):
    try:
        decodedPayload = jwt.decode(token, secretKey, algorithms="HS256")
        return decodedPayload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="The token is invalid")

def getCurrentUser(token: str = Depends(getToken), db: Session = Depends(get_db)):
    payload = verifyToken(token)
    userID = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == userID).first()
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user

@app.get("/")
def root():
    """
    **Description:** Simple health check.
    - **Auth:** None
    - **Returns:** 200 OK with welcome message.
    """
    return {"message": "Woohoo!"}



# HTTP
# get all tasks
@app.get("/tasks", response_model=List[schemas.TaskResponse], status_code=200)
def getTasks(done: bool | None = None, 
             db: Session = Depends(get_db), 
             currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Returns all tasks belonging to the authenticated user.
    - **Auth:** JWT Required.
    - **Query Params:** `done` (Optional bool) to filter by status.
    - **Logic:** Only returns tasks where `owner_id` matches `currentUser.id`.
    - **Returns:** 200 OK with list of tasks (Empty list `[]` if none found).
    """
    query = db.query(models.Task).filter(models.Task.owner_id == currentUser.id)
    if done is not None:
        query = query.filter(models.Task.done == done)
    results = query.all()
    return results

# get a singular task
@app.get("/tasks/{rTaskId}")
def getTask(rTaskId: int, 
            db: Session = Depends(get_db),
            currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Returns a specific task by its ID.
    - **Auth:** JWT Required.
    - **Logic:** 
        - Verifies task exists.
        - Verifies task belongs to the authenticated user.
    - **Returns:** 200 OK with Task object.
    - **Errors:** 404 Not Found: Task ID missing or owned by another user.
    """
    query = db.query(models.Task).filter(models.Task.id == rTaskId, models.Task.owner_id == currentUser.id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Task not found")
    return query

# add a new task
@app.post("/tasks")
def addTask(rTask: schemas.TaskCreate, 
            db: Session = Depends(get_db),
            currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Creates a new task for the authenticated user.
    - **Auth:** JWT Required.
    - **Requirements:** `title` (1-50 chars).
    - **Logic:** Automatically assigns `owner_id` from the current user's session.
    - **Returns:** 201 Created with saved Task object.
    """
    newTask = models.Task(**rTask.model_dump(), owner_id = currentUser.id)
    try:
        db.add(newTask)
        db.commit()
        db.refresh(newTask)
        return newTask
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code = 500, detail="Internal server error")

# update a task
@app.patch("/tasks/{rTaskId}")
def updateTask(rTaskId: int, 
               rUpdated: schemas.TaskUpdate, 
               db: Session = Depends(get_db),
               currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Partially updates an existing task.
    - **Auth:** JWT Required.
    - **Logic:** Verifies ownership before applying updates to `title` or `done`.
    - **Returns:** 200 OK with updated Task object.
    - **Errors:** 404 Not Found: Task ID missing or owned by another user.
    """
    query = db.query(models.Task).filter(models.Task.id == rTaskId, models.Task.owner_id == currentUser.id).first()
    if not query:
        raise HTTPException(status_code=404, detail=f"Task {rTaskId} not found")
    try:
        if rUpdated.title is not None:
            query.title = rUpdated.title
        if rUpdated.done is not None:
            query.done = rUpdated.done
        db.commit()
        db.refresh(query)
        return query
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
# delete all tasks
@app.delete("/tasks")
def deleteAllTasks(db: Session = Depends(get_db),
                   currentUser: models.User = Depends(getCurrentUser)):
    query = db.query(models.Task).filter(models.Task.owner_id == currentUser.id)
    """
    **Description:** Wipes all tasks for the authenticated user.
    - **Auth:** JWT Required.
    - **Logic:** Deletes all rows where `owner_id` matches `currentUser.id`.
    - **Returns:** 200 OK with success message.
    - **Errors:** 404 Not Found: User has no tasks to delete.
    """
    if query.count() == 0:
        raise HTTPException(status_code=404, detail="Tasks not found")
    try:
        query.delete(synchronize_session=False)
        db.commit()
        return {"message": "All tasks removed successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# delete a task
@app.delete("/tasks/{rTaskId}")
def deleteTask(rTaskId: int, 
               db: Session = Depends(get_db),
               currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Deletes a specific task.
    - **Auth:** JWT Required.
    - **Logic:** Verifies ownership before deletion.
    - **Returns:** 200 OK with success message.
    - **Errors:** 404 Not Found: Task ID missing or owned by another user.
    """
    query = db.query(models.Task).filter(models.Task.id == rTaskId, models.Task.owner_id == currentUser.id).first()
    if not query:
        raise HTTPException(status_code=404, detail=f"Task #{rTaskId} not found")
    try:
        db.delete(query)
        db.commit()
        return {"message": "Task removed successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users")
def getAllUsers(db: Session = Depends(get_db),
                currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Lists all registered users (Admin only).
    - **Auth:** JWT + Admin rights required.
    - **Returns:** 200 OK with list of User objects (passwords excluded).
    - **Errors:** 403 Forbidden: Authenticated user is not an admin.
    """
    query = db.query(models.User).all()
    if not currentUser.is_admin:
        raise HTTPException(403, detail="Missing administator permissions")
    if not query:
        raise HTTPException(404, detail="Couldn't find any users")
    return query

@app.get("/users/{rUserId}")
def getUser(rUserId: int, db: 
            Session = Depends(get_db),
            currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Returns details for a specific user (Admin only).
    - **Auth:** JWT + Admin rights required.
    - **Returns:** 200 OK with User object.
    - **Errors:** 
        - 403 Forbidden: Authenticated user is not an admin.
        - 404 Not Found: User ID does not exist.
    """
    query = db.get(models.User, rUserId)
    if not currentUser.is_admin and currentUser.id != query.id:
        raise HTTPException(403, detail="Missing administator permissions")
    if not query:
        raise HTTPException(404, detail=f"Couldn't find user #{rUserId}")
    return query

@app.post("/users/register") 
def registerUser(rUserDetails: schemas.UserDetails, 
                 db: Session = Depends(get_db)):
    """
    **Description:** Creates a new user account and hashes the password.
    - **Auth:** None
    - **Requirements:** 
        - `username`: Unique string (1-20 chars).
        - `password`: Plain text (will be hashed).
        - `admin`: Optional string (matches secret code for admin rights).
    - **Logic:** Sets `is_admin` to True if secret code matches, else False.
    - **Returns:** 201 Created with user ID and success message.
    - **Errors:** 
        - 400 Bad Request: Username already exists.
        - 401 Unauthorized: Admin code provided but incorrect.
    """
    userExists = db.query(models.User).filter(models.User.username == rUserDetails.username).first()
    if userExists:
        raise HTTPException(400, detail="User by this name already exists")
    newUser = models.User(
        username=rUserDetails.username,
        password=pbkdf2_sha256.hash(rUserDetails.password)
    )
    if rUserDetails.admin:
        if rUserDetails.admin == adminCode:
            newUser.is_admin = True
        else:
            raise HTTPException(401, detail="Incorrect admin code.")
    else:
        newUser.is_admin = False

    try:
        db.add(newUser)
        db.commit()
        db.refresh(newUser)
        return {"message": "User created successfully!", "id": newUser.id, "admin": newUser.is_admin}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(500, detail="Internal server error")

@app.post("/users/login")
def loginUser(rUserDetails: schemas.UserDetails, 
              db: Session = Depends(get_db)):
    query = db.query(models.User).filter(models.User.username == rUserDetails.username).first()
    """
    **Description:** Authenticates user and generates a JWT access token.
    - **Auth:** None
    - **Requirements:** Valid `username` and `password`.
    - **Returns:** 200 OK with JWT token and role-specific message.
    - **Errors:** 
        - 400 Bad Request: Username not found.
        - 401 Unauthorized: Invalid password.
    """
    if not query: 
        raise HTTPException(400, detail="Wrong credentials")
    if not pbkdf2_sha256.verify(rUserDetails.password, query.password):
        raise HTTPException(401, detail="Invalid credentials")
    return {"message":"Logged in successfully!", 
            "admin_status":query.is_admin ,
            "token":createToken(query.id)}
    
@app.delete("/users/{rUserId}")
def deleteUser(rUserId: int, db: Session = Depends(get_db),
               currentUser: models.User = Depends(getCurrentUser)):
    """
    **Description:** Deletes a user account.
    - **Auth:** JWT Required.
    - **Logic:** 
        - Admins can delete any user.
        - Regular users can only delete their own account.
    - **Returns:** 200 OK with success message.
    - **Errors:** 
        - 403 Forbidden: Attempting to delete another user without admin rights.
        - 404 Not Found: User ID does not exist.
    """
    query = db.query(models.User).filter(models.User.id == rUserId).first()
    if not query:
        raise HTTPException(404, detail=f"Couldn't find user #{rUserId}")
    if not currentUser.is_admin and currentUser.id != query.id:
        raise HTTPException(403, detail="Missing administator permissions")
    try:
        db.delete(query)
        db.commit()
        return {"message":f"Deleted user #{rUserId} successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(500, detail="Internal server error")