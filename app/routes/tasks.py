from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.extensions import get_db
from app.schemas.task import TaskCreate, TaskResponse
from app.models.task import Task  # Note: rename Tasks to Task for consistency
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
def create_task(
        task: TaskCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    datetime_str = f"{task.date} {task.time}"
    try:
        task_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")

    db_task = Task(task=task.task, date=task_datetime, time=task_datetime)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    tasks = db.query(Task).all()
    return tasks