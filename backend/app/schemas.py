from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    done: bool = False


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=50)
    done: bool | None = None


class UserDetails(BaseModel):
    username: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1)
    admin_code: Optional[str] = None


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=20)
    password: str | None = Field(default=None, min_length=1)
    admin_code: Optional[str] = None


class TaskResponse(ORMModel):
    id: int
    title: str
    done: bool
    owner_id: int


class LoginResponse(BaseModel):
    message: str
    id: int
    is_admin: bool
    token: str


class UserResponse(ORMModel):
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