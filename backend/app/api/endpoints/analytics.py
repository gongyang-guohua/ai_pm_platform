from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project, Task, Material
from app.core.database import get_db
from app.core.llm import llm_service
from typing import Dict, Any

router = APIRouter()

@router.get("/projects/{project_id}/stats")
async def get_project_stats(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get consolidated performance stats for a project.
    """
    # Fetch project with tasks and materials
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.tasks).selectinload(Task.materials))
    )
    result = await db.execute(stmt)
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Calculate EVA metrics
    # PV (Planned Value) = Original Duration * rate
    # AC (Actual Cost) = Actual Cost field
    # EV (Earned Value) = Earned Value field or calculated
    
    rate = 100.0 # Standard hourly rate for calculation
    
    pv = sum(t.planned_value or (t.original_duration or 0) * rate for t in project.tasks)
    
    # AC is directly tracked or calculated
    ac_materials = sum(sum(m.total_price or 0 for m in (t.materials or [])) for t in project.tasks)
    
    # If actual_cost is stored on task, use it. Otherwise approximate from duration?
    # We will use the 'actual_cost' field on Task which we added.
    ac = sum(t.actual_cost or 0 for t in project.tasks)
    # If actual_cost is 0, maybe try to calculate from materials + implied labor?
    if ac == 0 and ac_materials > 0:
        ac = ac_materials # simplified
        
    ev = sum(t.earned_value or 0 for t in project.tasks)
    
    # Fallback for EV if not explicitly calculated in backend yet
    if ev == 0:
         ev = sum((t.original_duration or 0) * rate for t in project.tasks if t.status == 'completed')

    spi = ev / pv if pv > 0 else 1.0
    cpi = ev / ac if ac > 0 else 1.0
    
    return {
        "project_id": project_id,
        "performance": {
            "spi": spi,
            "cpi": cpi,
            "pv": pv,
            "ev": ev,
            "ac": ac,
        },
        "task_summary": {
            "total": len(project.tasks),
            "completed": len([t for t in project.tasks if t.status == 'completed']),
            "in_progress": len([t for t in project.tasks if t.status == 'in_progress']),
            "stalled": len([t for t in project.tasks if t.status == 'stalled']),
        },
        "cost_summary": {
            "materials": ac_materials,
            "labor": ac - ac_materials,
            "total": ac
        }
    }

@router.get("/portfolio/stats")
async def get_portfolio_stats(db: AsyncSession = Depends(get_db)):
    """
    Get aggregated stats for the entire portfolio.
    """
    result = await db.execute(select(Project))
    projects = result.scalars().all()
    
    # In a real app, we'd do complex aggregation
    return {
        "total_projects": len(projects),
        "status_distribution": {
            "planning": len([p for p in projects if p.status == 'planning']),
            "active": len([p for p in projects if p.status == 'active']),
            "completed": len([p for p in projects if p.status == 'completed']),
        }
    }

@router.post("/projects/{project_id}/report")
async def generate_project_report(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generate an AI-powered status report for the project.
    """
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.tasks))
    )
    result = await db.execute(stmt)
    project = result.scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Metrics
    total_tasks = len(project.tasks)
    completed_tasks = len([t for t in project.tasks if t.status == 'completed'])
    in_progress = len([t for t in project.tasks if t.status == 'in_progress'])
    
    prompt = f"""
    You are a Senior Project Manager. Generate a professional Project Status Report for the following project.
    
    Project Title: {project.title}
    Industry: {project.industry or 'General'}
    Project Status: {project.status}
    Description: {project.description}
    
    Key Metrics:
    - Total Tasks: {total_tasks}
    - Completed Tasks: {completed_tasks}
    - Tasks In Progress: {in_progress}
    - Tasks Not Started/Stalled: {total_tasks - completed_tasks - in_progress}
    
    Please structure the report with the following sections using Markdown:
    # {project.title} - Status Report
    ## 1. Executive Summary
    ## 2. Progress Overview
    ## 3. Risk Assessment (Theoretical based on project type and status)
    ## 4. Recommendations for Next Steps
    
    Keep the tone professional, concise, and action-oriented.
    """

    try:
        report_content = await llm_service.generate_text(prompt)
        return {"report": report_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
