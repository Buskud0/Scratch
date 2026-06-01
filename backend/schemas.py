from pydantic import BaseModel
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    done: bool | None = False

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

class UserDetails(BaseModel):
    username: str
    password: str
    admin: Optional[str] = False

class TaskResponse(BaseModel):
    id: int
    title: str
    done: bool
    owner_id: int

class LoginResponse(BaseModel):
    message: str
    id: int
    is_admin: bool
    token: str

class UserResponse(BaseModel):
    id: int
    is_admin: bool
    username: str
    
class RegisterResponse(BaseModel):
    message: str
    id: int
    is_admin: bool

class DeleteUserResponse(BaseModel):
    message: str
    username: str

class Config:
    from_attributes = True