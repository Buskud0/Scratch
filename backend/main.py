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
from pydantic import BaseModel
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

# Pydantic model (rules)
class Task(BaseModel):
    id: int | None = None
    title: str
    done: bool = False

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

# a temporary database
tasks = [
    Task(id=0, title="task0", done=False),
    Task(id=1, title="task1", done=False),
    Task(id=2, title="task2", done=True)
]


@app.get("/")
def root():
    return {"message": "Database is ready!"}

# get all tasks (with query parameter)
@app.get("/tasks")
def getTasks(done: bool | None = None, db: Session = Depends(get_db)):
    if done is not None:
        return [task for task in tasks if task.done == done]
    return tasks

# get a singular task
@app.get("/tasks/{task_id}")
def getTask(task_id: int, db: Session = Depends(get_db)):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")
        

# add a new task
@app.post("/tasks")
def addTask(new: Task, db: Session = Depends(get_db)):
    new.id = len(tasks)
    tasks.append(new)
    return new

# update a task
@app.patch("/tasks/{task_id}")
def updateTask(task_id: int, updated: TaskUpdate, db: Session = Depends(get_db)):
    for task in tasks:
        if task.id == task_id:
            if updated.title is not None:
                task.title = updated.title
            if updated.done is not None:
                task.done = updated.done
            return task
    raise HTTPException(status_code=404, detail="Task not found")
        
# delete a task
@app.delete("/tasks/{task_id}")
def deleteTask(task_id: int, db: Session = Depends(get_db)):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            return {"message": "Task removed successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

