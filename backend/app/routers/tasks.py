from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import commit_or_500, get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_owned_task(db: Session, user: models.User, task_id: int) -> models.Task:
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.owner_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.get("", response_model=List[schemas.TaskResponse])
def get_tasks(
    done: bool | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Task).filter(models.Task.owner_id == current_user.id)
    if done is not None:
        query = query.filter(models.Task.done == done)
    return query.all()


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_task(db, current_user, task_id)


@router.post("", response_model=schemas.TaskResponse, status_code=201)
def add_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_task = models.Task(**task.model_dump(), owner_id=current_user.id)
    db.add(new_task)
    commit_or_500(db)
    db.refresh(new_task)
    return new_task


@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    updates: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(db, current_user, task_id)
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    commit_or_500(db)
    db.refresh(task)
    return task


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db.query(models.Task).filter(models.Task.owner_id == current_user.id).delete(
        synchronize_session=False
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT, media_type="application/json")


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(db, current_user, task_id)
    db.delete(task)
    commit_or_500(db)
    return {"message": "Task removed successfully"}