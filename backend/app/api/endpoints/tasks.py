from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.services.scheduling_engine import SchedulingEngine
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
        if field in valid_columns and field != 'dependencies':
            setattr(task, field, value)
        elif field == "estimated_hours" and value is not None: # Compatibility mapping
            setattr(task, "original_duration", value)
            setattr(task, "estimated_hours", value)

    # Handle Dependencies
    # Handle Dependencies
    if task_in.dependencies is not None:
        # Clear existing predecessors
        from app.models.project import TaskRelationship
        from sqlalchemy import delete
        
        # Delete existing predecessors where this task is the successor
        await db.execute(
            delete(TaskRelationship).where(TaskRelationship.successor_id == task_id)
        )
        
        # Add new dependencies
        for dep in task_in.dependencies:
            new_rel = TaskRelationship(
                project_id=task.project_id,
                predecessor_id=dep.target_id,
                successor_id=task_id,
                type=dep.relation,
                lag=dep.lag
            )
            db.add(new_rel)

    
    await db.commit()
    await db.refresh(task)

    # Auto-Schedule / CPM Calculation
    # If dependencies, duration, or start date changed, we need to re-calculate the project schedule.
    # This ensures "logical links" (predecessors) actually move successor dates.
    should_schedule = False
    if task_in.dependencies is not None:
        should_schedule = True
    else:
        # Check if critical fields were updated
        triggers = ['original_duration', 'estimated_hours', 'planned_start', 'constraint_type', 'constraint_date']
        for field in triggers:
            if field in update_data:
                should_schedule = True
                break
    
    if should_schedule:
        try:
            # Re-run CPM
            engine = SchedulingEngine(db, task.project_id)
            await engine.load_data()
            
            # Determine Project Start (Anchor) based on earliest existing task
            # This prevents everything resetting to "Now" if we use datetime.now()
            project_start = datetime.now()
            if engine.tasks:
                starts = [t.planned_start for t in engine.tasks.values() if t.planned_start]
                if starts:
                    project_start = min(starts)
            
            # Use naive project_start if TZ issues arise, or ensure robust checking? 
            # engine handles it.
            engine.calculate_dates(project_start)
            
            # Sync Planned Dates with Calculated Dates (CPM)
            # This ensures the Gantt chart (which uses planned_*) reflects the schedule.
            for t in engine.tasks.values():
                if t.early_start:
                    t.planned_start = t.early_start
                if t.early_finish:
                    t.planned_end = t.early_finish

            await engine.save_dates()
            await db.commit()
            await db.refresh(task) # Get updated dates
        except Exception as e:
            print(f"Warning: Auto-scheduling failed: {e}")
            # We continue to return the task 

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
