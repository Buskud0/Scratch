from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Task(Base):
    __tablename__ = "tasks"

    owner_id = Column(Integer, ForeignKey("users.id"))
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(50), nullable=False)
    done = Column(Boolean, default = False)
    owner = relationship("User", back_populates=("tasks"))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(20), nullable=False)
    password = Column(String(255), nullable=False)
    tasks = relationship("Task", back_populates="owner_id")