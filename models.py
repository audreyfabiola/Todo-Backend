from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    hashedpassword = Column(String)

    todos = relationship("Todo", back_populates="owner")


class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True)
    title = Column(String, index=True)
    completed = Column(Boolean)
    isEditing = Column(Boolean)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="todos")

class SessionInfo(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True)
