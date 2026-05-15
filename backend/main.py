# Scratch TO-DO app!

#1. Create a virtual environment
# py -m venv env
# .\env\Scripts\Activate.ps1

#2. Pip package manager
# pip list (to see installed packages)
# pip install "fastapi[standard]"
# pip install sqlalchemy pymysql

#GIT
# git checkout develop <--- switches branch to develop
# git push origin develop <--- pushes changes to develop

# git checkout -b feature-branch <--- creates new branch
# git merge feature-branch <--- merges branch

# > fastapi dev

from fastapi import FastAPI, HTTPException, Depends
import schemas
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models

Base.metadata.create_all(bind=engine)
app = FastAPI()

# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Woohoo!"}

# get all tasks (with query parameter)
@app.get("/tasks")
def getTasks(rDone: bool | None = None, db: Session = Depends(get_db)):
    tasks = db.query(models.Task)
    if tasks.count() == 0:
        raise HTTPException(status_code=404, detail="Tasks not found")
    if rDone is not None:
        tasks = tasks.filter(models.Task.done == rDone).all()
    return tasks.all()

# get a singular task
@app.get("/tasks/{rTaskId}")
def getTask(rTaskId: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, rTaskId)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
        

# add a new task
@app.post("/tasks")
def addTask(rTask: schemas.TaskCreate, db: Session = Depends(get_db)):
    newTask = models.Task(**rTask.model_dump())
    try:
        db.add(newTask)
        db.commit()
        db.refresh(newTask)
        return newTask
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = 500, detail="Couldn't upload task to the database")

# update a task
@app.patch("/tasks/{rTaskId}")
def updateTask(rTaskId: int, rUpdated: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(models.Task, rTaskId)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        if rUpdated.title is not None:
            task.title = rUpdated.title
        if rUpdated.done is not None:
            task.done = rUpdated.done
        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't update task in the database")
        
# delete all tasks
@app.delete("/tasks")
def deleteAllTasks(db: Session = Depends(get_db)):
    tasks = db.query(models.Task)
    if tasks.count() == 0:
        raise HTTPException(status_code=404, detail="Tasks not found")
    try:
        tasks.delete()
        db.commit()
        return {"message": "All tasks removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't delete all tasks from the database")

# delete a task
@app.delete("/tasks/{rTaskId}")
def deleteTask(rTaskId: int, db: Session = Depends(get_db)):
    task = db.get(models.Task, rTaskId)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        db.delete(task)
        db.commit()
        return {"message": "Task removed successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Couldn't delete task from the database")
