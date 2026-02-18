from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.models.project import Project, Task, Material
from app.schemas.project import Task as TaskSchema, Material as MaterialSchema
from app.core.database import get_db
from typing import List

router = APIRouter()

@router.patch("/tasks/{task_id}/progress", response_model=TaskSchema)
async def update_task_progress(
    task_id: int, 
    actual_hours: float, 
    status: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Update the progress and status of a specific task.
    """
    result = await db.execute(select(Task).filter(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.actual_hours = actual_hours
    task.status = status
    await db.commit()
    await db.refresh(task)
    return task

@router.get("/projects/{project_id}/materials", response_model=List[MaterialSchema])
async def get_project_materials(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get all materials associated with a project (across all tasks).
    """
    result = await db.execute(
        select(Material)
        .join(Task)
        .filter(Task.project_id == project_id)
    )
    return result.scalars().all()

@router.get("/projects/{project_id}/costs")
async def get_project_costs(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Calculate the total cost of a project based on its materials.
    """
    result = await db.execute(
        select(Material)
        .join(Task)
        .filter(Task.project_id == project_id)
    )
    materials = result.scalars().all()
    
    total_cost = sum(m.total_price for m in materials)
    by_category = {}
    for m in materials:
        by_category[m.category] = by_category.get(m.category, 0) + m.total_price
        
    return {
        "project_id": project_id,
        "total_cost": total_cost,
        "cost_breakdown": by_category
    }

@router.get("/projects/{project_id}/critical-path")
async def get_critical_path(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Calculate the critical path and scheduling details (ES, EF, LS, LF) using CPM.
    """
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Task)
        .filter(Task.project_id == project_id)
        .options(selectinload(Task.materials))
    )
    tasks = result.scalars().all()
    if not tasks:
        return {"critical_path": [], "schedule": []}

    # Map for easy access
    id_to_task = {t.id: t for t in tasks}
    schedule = {t.id: {"title": t.title, "es": 0, "ef": 0, "ls": float('inf'), "lf": float('inf'), "slack": 0} for t in tasks}

    # Forward Pass
    def calculate_forward(task_id, visited=None):
        if visited is None: visited = set()
        if task_id in visited: return schedule[task_id]["ef"]
        visited.add(task_id)
        
        task = id_to_task[task_id]
        max_prev_ef = 0
        
        # dependencies is a list of dicts: {"target_id": ..., "relation": "FS", "lag": 0}
        deps = task.dependencies or []
        for dep_info in deps:
            target_id = None
            lag = 0
            if isinstance(dep_info, dict):
                target_id = dep_info.get("target_id")
                lag = dep_info.get("lag", 0)
            elif isinstance(dep_info, int): # Fallback
                target_id = dep_info
            
            if target_id and target_id in id_to_task:
                # Basic FS logic: Start depends on Finish of predecessor
                prev_ef = calculate_forward(target_id, visited)
                max_prev_ef = max(max_prev_ef, prev_ef + lag)
        
        schedule[task_id]["es"] = max_prev_ef
        schedule[task_id]["ef"] = max_prev_ef + (task.estimated_hours or 0)
        return schedule[task_id]["ef"]

    for t in tasks:
        calculate_forward(t.id)

    # Project duration
    project_finish = max(s["ef"] for s in schedule.values()) if schedule else 0

    # Backward Pass
    # Precompute successors
    successors = {t.id: [] for t in tasks}
    for t in tasks:
        deps = t.dependencies or []
        for dep_info in deps:
            target_id = None
            if isinstance(dep_info, dict):
                target_id = dep_info.get("target_id")
            elif isinstance(dep_info, int):
                target_id = dep_info
            
            if target_id and target_id in successors:
                successors[target_id].append(t.id)

    def calculate_backward(task_id, visited=None):
        if visited is None: visited = set()
        if task_id in visited: return schedule[task_id]["ls"]
        visited.add(task_id)
        
        task = id_to_task[task_id]
        if not successors[task_id]:
            min_next_ls = project_finish
        else:
            min_next_ls = min(calculate_backward(sid, visited) for sid in successors[task_id])
        
        schedule[task_id]["lf"] = min_next_ls
        schedule[task_id]["ls"] = min_next_ls - (task.estimated_hours or 0)
        schedule[task_id]["slack"] = schedule[task_id]["ls"] - schedule[task_id]["es"]
        return schedule[task_id]["ls"]

    for t in tasks:
        calculate_backward(t.id)

    critical_path = [t.id for t in tasks if abs(schedule[t.id]["slack"]) < 0.001]
    
    return {
        "project_id": project_id,
        "project_duration": project_finish,
        "critical_path": critical_path,
        "schedule": schedule
    }
