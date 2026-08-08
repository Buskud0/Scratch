from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.deps import commit_or_500
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["authentication"])


def _resolve_user_by_username(db: Session, username: str) -> models.User | None:
    return (
        db.query(models.User).filter(models.User.username == username).first()
    )


@router.post("/register", response_model=schemas.RegisterResponse, status_code=201)
def register_user(
    user: schemas.UserDetails,
    db: Session = Depends(get_db),
):
    if _resolve_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="User by this name already exists")

    new_user = models.User(username=user.username, password=hash_password(user.password))
    if user.admin_code == settings.admin_code:
        new_user.is_admin = True
    elif user.admin_code:
        raise HTTPException(status_code=401, detail="Incorrect admin code.")

    db.add(new_user)
    commit_or_500(db)
    db.refresh(new_user)
    return {
        "message": "User created successfully!",
        "id": new_user.id,
        "is_admin": new_user.is_admin,
    }


@router.post("/login", response_model=schemas.LoginResponse)
def login_user(
    user: schemas.UserDetails,
    db: Session = Depends(get_db),
):
    record = _resolve_user_by_username(db, user.username)
    if not record:
        raise HTTPException(status_code=400, detail="Wrong credentials")
    if not verify_password(user.password, record.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {
        "message": "Logged in successfully!",
        "id": record.id,
        "is_admin": record.is_admin,
        "token": create_access_token(record.id),
    }