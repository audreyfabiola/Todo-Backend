from sqlalchemy.orm import Session
from . import models, schemas

# CRUD operations for User model

# CRUD operations for User
def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + ""  # Example hashing
    db_user = models.User(email=user.email, username=user.username, hashedpassword=fake_hashed_password,
    )
   
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# CRUD operations for Todo model

def create_todo_for_user(db: Session, user_id: int, todo: schemas.TodoCreate):
    db_todo = models.Todo(**todo.dict(), user_id=user_id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def get_todos_for_user(db: Session, user_id: int):
    return db.query(models.Todo).filter(models.Todo.user_id == user_id).all()

def get_todo_for_user(db: Session, user_id: int, todo_id: int):
    return db.query(models.Todo).filter(models.Todo.user_id == user_id, models.Todo.id == todo_id).first()

def get_todos(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Todo).offset(skip).limit(limit).all()

def update_todo_for_user(db: Session, user_id: int, todo_id: int, todo: schemas.TodoBase):
    db_todo = db.query(models.Todo).filter(models.Todo.user_id == user_id, models.Todo.id == todo_id).first()
    if db_todo:
        for var, value in vars(todo).items():
            if value is not None:
                setattr(db_todo, var, value)
        db.commit()
        db.refresh(db_todo)
    return db_todo

def delete_todo_for_user(db: Session, user_id: int, todo_id: int):
    db_todo = db.query(models.Todo).filter(models.Todo.user_id == user_id, models.Todo.id == todo_id).first()
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo

