# Scratch TO-DO app!
# https://fastapi.tiangolo.com/

#1. Create a virtual environment
# py -m venv env
# .\env\Scripts\Activate.ps1

#2. Pip package manager
# pip list (to see installed packages)
# pip install "fastapi[standard]"

# > fastapi dev

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    id: int | None = None
    title: str
    completed: bool = False

tasks = [
    Task(id=0, title="task0", completed=False),
    Task(id=1, title="task1", completed=False),
    Task(id=2, title="task2", completed=True)
]

@app.get("/tasks")
def getTasks():
    return tasks

@app.post("/tasks")
def addTask(task: Task):
    task.id = len(tasks)
    tasks.append(task)
    return task

@app.patch("/tasks/{task_id}")
def completeTask(task_id: int):
    for task in tasks:
        if task_id == task.id:
            task.completed = not task.completed
            return task