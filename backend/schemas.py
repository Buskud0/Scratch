from pydantic import BaseModel
from typing import Optional

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

class UserDetails(BaseModel):
    username: str
    password: str
    admin: Optional[str] = False