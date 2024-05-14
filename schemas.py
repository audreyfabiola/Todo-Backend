from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class TodoBase(BaseModel):
    title: str
    completed: bool
    isEditing: bool

class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class UserWithTodos(User):
    todos: List[Todo] = []

    class Config:
        orm_mode = True

class SessionData(BaseModel):
    email: str
