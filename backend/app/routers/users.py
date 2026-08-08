from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.deps import commit_or_500, get_current_user, require_admin
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _is_owner_or_admin(user: models.User, target: models.User) -> bool:
    return user.is_admin or user.id == target.id


@router.get("", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(status_code=404, detail="Couldn't find any users")
    return users


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = db.get(models.User, user_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Couldn't find user #{user_id}")
    if not _is_owner_or_admin(current_user, record):
        raise HTTPException(status_code=403, detail="Missing administrator permissions")
    return record


@router.patch("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    updates: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = db.query(models.User).filter(models.User.id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Couldn't find user #{user_id}")
    if not _is_owner_or_admin(current_user, record):
        raise HTTPException(status_code=403, detail="Missing administrator permissions")

    if updates.username is not None:
        record.username = updates.username
    if updates.password is not None:
        record.password = hash_password(updates.password)
    if updates.admin_code:
        if updates.admin_code == settings.admin_code:
            record.is_admin = True
        elif updates.admin_code == "false":
            record.is_admin = False
        else:
            raise HTTPException(status_code=401, detail="Incorrect admin code.")

    commit_or_500(db)
    db.refresh(record)
    return record


@router.delete("/{user_id}", response_model=schemas.DeleteUserResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = db.query(models.User).filter(models.User.id == user_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Couldn't find user #{user_id}")
    if not _is_owner_or_admin(current_user, record):
        raise HTTPException(status_code=403, detail="Missing administrator permissions")

    username = record.username
    db.delete(record)
    commit_or_500(db)
    return {"message": f"Deleted user #{user_id} successfully", "username": username}