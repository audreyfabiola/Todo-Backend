from fastapi import Depends, FastAPI, HTTPException, Response, Request, Cookie
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from uuid import UUID, uuid4

from fastapi.middleware.cors import CORSMiddleware
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters

import requests

from . import crud, models, schemas
from .database import SessionLocal, engine
from .models import SessionInfo


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Define allowed origins
origins = [
    "http://localhost:5173",  
    "localhost:5173"
]

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create User
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

# Read all users
@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Read user
@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Read all todos
@app.get("/todos/", response_model=List[schemas.Todo])
def read_todos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    todos = crud.get_todos(db, skip=skip, limit=limit)
    return todos

# Create todo for user
@app.post("/users/{user_id}/todos/", response_model=schemas.Todo)
def create_todo_for_user(user_id: int, todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo_for_user(db=db, user_id=user_id, todo=todo)

# Get todos for user
@app.get("/users/{user_id}/todos/", response_model=List[schemas.Todo])
def get_todos_for_user(user_id: int, db: Session = Depends(get_db)):
    return crud.get_todos_for_user(db=db, user_id=user_id)

# Get todo for user
@app.get("/users/{user_id}/todos/{todo_id}", response_model=schemas.Todo)
def get_todo_for_user(user_id: int, todo_id: int, db: Session = Depends(get_db)):
    return crud.get_todo_for_user(db=db, user_id=user_id, todo_id=todo_id)

# Update todo for user
@app.put("/users/{user_id}/todos/{todo_id}", response_model=schemas.Todo)
def update_todo_for_user(user_id: int, todo_id: int, todo: schemas.TodoBase, db: Session = Depends(get_db)):
    return crud.update_todo_for_user(db=db, user_id=user_id, todo_id=todo_id, todo=todo)

# Delete todo for user
@app.delete("/users/{user_id}/todos/{todo_id}")
def delete_todo_for_user(user_id: int, todo_id: int, db: Session = Depends(get_db)):
    return crud.delete_todo_for_user(db=db, user_id=user_id, todo_id=todo_id)

@app.post("/login/")
def login_user(user: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    # Check if the user exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Retrieve or create session info for the user
    session_info = db.query(SessionInfo).filter(SessionInfo.email == user.email).first()
    if not session_info:
        # If session info doesn't exist, create a new session
        try:
            # Make a request to create a session for the user
            create_session_url = f"http://127.0.0.1:8000/create_session/{user.email}"
            create_session_response = requests.post(create_session_url)

            # Check if the session creation was successful
            if create_session_response.status_code == 200:
                # Retrieve the session ID from the response
                session_id = create_session_response.text

                # # Attach session ID to the response as a cookie
                # cookie.attach_to_response(response, session_id)

                return {"success": True, "user_id": db_user.id, "session_id": session_id}
            else:
                raise HTTPException(status_code=500, detail="Failed to create session")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"success": True, "user_id": db_user.id, "session_id": session_info.session_id}

# Session
class SessionData(BaseModel):
    username: str


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

@app.post("/create_session/{email}")
async def create_session(email: str, response: Response, db: Session = Depends(get_db)):
    try:
        # Generate session ID (randomly generated string)
        session_id = str(uuid4())

        # Create a record in the database with the session ID and email
        db_session_info = SessionInfo(session_id=session_id, email=email)
        db.add(db_session_info)
        db.commit()

        return session_id
    except Exception as e:
        # Handle exceptions
        return {"error": str(e)}

    
@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data

@app.delete("/delete_session/{session_id}")
async def del_session(session_id: str, db: Session = Depends(get_db)):
    try:
        # Check if session exists with provided session ID
        session_info = db.query(SessionInfo).filter(SessionInfo.session_id == session_id).first()
        if session_info:
            db.delete(session_info)
            db.commit()
            return "Deleted session successfully"
        else:
            raise HTTPException(status_code=404, detail="Session not found with provided session ID")
    except Exception as e:
        # Handle any exceptions
        return {"error": str(e)}
    
# POST method handler for login
# @app.post("/login/")
# async def login(request: Request):
#     # Implement your login logic here
#     return {"message": "Login endpoint reached"}

# @app.options("/login/")
# async def options_login(request: Request):
#     return Response(headers={
#         "Allow": "POST",
#         "Access-Control-Allow-Origin": "*",
#         "Access-Control-Allow-Methods": "POST",
#         "Access-Control-Allow-Headers": "Content-Type",
#     })
