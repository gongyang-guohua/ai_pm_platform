from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Task, Material
from app.schemas.project import Task as TaskSchema, TaskUpdate, TaskCreate
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=TaskSchema)
async def create_task(task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new task.
    """
    db_task = Task(
        project_id=task_in.project_id,
        title=task_in.title,
        description=task_in.description,
        task_type=task_in.task_type,
        status=task_in.status,
        priority=task_in.priority,

        original_duration=task_in.original_duration if task_in.original_duration else task_in.estimated_hours,
        discipline=task_in.discipline,
        is_deliverable=task_in.is_deliverable
    )
    db.add(db_task)
    await db.commit()
    
    # Reload with relations for the response schema validation
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Task)
        .filter(Task.id == db_task.id)
        .options(
            selectinload(Task.materials),
            selectinload(Task.relationships_pred)
        )
    )
    return result.scalars().first()

@router.get("/{task_id}", response_model=TaskSchema)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific task by ID.
    """
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Task)
        .filter(Task.id == task_id)
        .options(
            selectinload(Task.materials),
            selectinload(Task.relationships_pred)
        )
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskSchema)
async def update_task(task_id: int, task_in: TaskUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update a task.
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_in.model_dump(exclude_unset=True)
    # Get list of valid columns on the model
    valid_columns = task.__table__.columns.keys()
    for field, value in update_data.items():
        if field in valid_columns:
            setattr(task, field, value)
        elif field == "estimated_hours": # Compatibility mapping
            setattr(task, "original_duration", value)
        # Skip dependencies or other properties that don't have setters
    
    await db.commit()
    await db.refresh(task)
    
    # Reload with materials
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Task)
        .filter(Task.id == task_id)
        .options(
            selectinload(Task.materials),
            selectinload(Task.relationships_pred)
        )
    )
    return result.scalars().first()

@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a task.
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return {"message": "Success"}
