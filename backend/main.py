# Scratch TO-DO app!
# https://fastapi.tiangolo.com/

#1. Create a virtual environment
# py -m venv env
# .\env\Scripts\Activate.ps1

#2. Pip package manager
# pip list (to see installed packages)
# pip install "fastapi[standard]"

#GIT
# git checkout develop <--- switches branch to develop
# git push origin develop <--- pushes changes to develop

# git checkout -b feature-branch <--- creates new branch
# git merge feature-branch <--- merges branch

# > fastapi dev

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# rules for tasks
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

# get all tasks (with query parameter)
@app.get("/tasks")
def getTasks(done: bool | None = None):
    if done is not None:
        return [task for task in tasks if task.done == done]
    return tasks

# get a singular task
@app.get("/tasks/{task_id}")
def getTask(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")
        

# add a new task
@app.post("/tasks")
def addTask(new: Task):
    new.id = len(tasks)
    tasks.append(new)
    return new

# update a task
@app.patch("/tasks/{task_id}")
def updateTask(task_id: int, updated: TaskUpdate):
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
def deleteTask(task_id: int):
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
            raise HTTPException(status_code=200)
    raise HTTPException(status_code=404, detail="Task not found")