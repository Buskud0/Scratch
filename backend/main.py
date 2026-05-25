# Scratch TO-DO app!
# > fastapi dev - run the app

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from passlib.hash import pbkdf2_sha256
import models
import schemas
import jwt
import os
from datetime import datetime, timezone, timedelta
from fastapi.security import OAuth2PasswordBearer

Base.metadata.create_all(bind=engine)
app = FastAPI()
secretKey = os.getenv("SECRET_KEY")
getToken = OAuth2PasswordBearer(tokenUrl="login")

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def createToken(id: str):
    payload = {
        "sub": id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, secretKey, algorithm="HS256")
    return token

def verifyToken(token: str):
    try:
        decodedPayload = jwt.decode(token, secretKey, algorithm="HS256")
        return decodedPayload
    except jwt.InvalidTokenError:
        raise HTTPException(404, "The token is invalid")

def getCurrentUser(token: str = Depends(getToken), db: Session = Depends(get_db)):
    payload = verifyToken(token)
    userID = payload.get("sub")
    user = db.query(models.User).filter(models.User.id == userID).first()
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user

@app.get("/")
def root():
    return {"message": "Woohoo!"}

# get all tasks (with query parameter)
@app.get("/tasks")
def getTasks(rDone: bool | None = None, 
             db: Session = Depends(get_db), 
             currentUser: models.User = Depends(getCurrentUser)):
    query = db.query(models.Task).filter(models.Task.owner_id == currentUser.id)
    if query.count() == 0:
        raise HTTPException(status_code=404, detail="Tasks not found")
    if rDone is not None:
        query = query.filter(models.Task.done == rDone).all()
    return query

# get a singular task
@app.get("/tasks/{rTaskId}")
def getTask(rTaskId: int, 
            db: Session = Depends(get_db),
            currentUser: models.User = Depends(getCurrentUser)):
    query = db.query(models.Task).filter(models.Task.id == rTaskId, models.Task.owner_id == currentUser.id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Task not found")
    return query

# add a new task
@app.post("/tasks")
def addTask(rTask: schemas.TaskCreate, 
            db: Session = Depends(get_db),
            currentUser: models.User = Depends(getCurrentUser)):
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
    if query.count() == 0:
        raise HTTPException(status_code=404, detail="Tasks not found")
    try:
        query.delete()
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
    query = db.query(models.Task).filter(models.Task.id == rTaskId, models.Task.owner_id == currentUser.id)
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

@app.get("/users") #todo: admin check
def getAllUsers(db: Session = Depends(get_db),
                currentUser: models.User = Depends(getCurrentUser)):
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(404, detail="Couldn't find any users")
    return users

@app.get("/users/{rUserId}") #todo: admin check
def getUser(rUserId: int, db: 
            Session = Depends(get_db),
            currentUser: models.User = Depends(getCurrentUser)):
    user = db.get(models.User, rUserId)
    if not user:
        raise HTTPException(404, detail=f"Couldn't find user #{rUserId}")
    return user

@app.post("/users/register") 
def registerUser(rUserDetails: schemas.UserDetails, 
                 db: Session = Depends(get_db)):
    userExists = db.query(models.User).filter(models.User.username == rUserDetails.username).first()
    if userExists:
        raise HTTPException(400, detail="User by this name already exists")
    rUserDetails.password = pbkdf2_sha256.hash(rUserDetails.password)
    newUser = models.User(**rUserDetails.model_dump())
    try:
        db.add(newUser)
        db.commit()
        db.refresh(newUser)
        return {"message": "User created successfully!", "id": newUser.id}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(500, detail="Internal server error")

@app.post("/users/login")
def loginUser(rUserDetails: schemas.UserDetails, 
              db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == rUserDetails.username).first()
    if not user: 
        raise HTTPException(400, detail="Wrong credentials")
    if not pbkdf2_sha256.verify(rUserDetails.password, user.password):
        raise HTTPException(401, detail="Invalid credentials")
    return {"token":createToken(user.id)}
    
@app.delete("/users/{rUserId}") #todo: admin check OR user
def deleteUser(rUserId: int, db: Session = Depends(get_db),
               currentUser: models.User = Depends(getCurrentUser)):
    query = db.query(models.User).filter(models.User.UserId == rUserId, models.User.UserId == currentUser.id)
    if not query:
        raise HTTPException(404, detail=f"Couldn't find user #{rUserId}")
    try:
        db.delete(query)
        db.commit()
        return {"message":f"Deleted user #{rUserId} successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise HTTPException(500, detail="Internal server error")