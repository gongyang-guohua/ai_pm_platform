from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project, Task
from app.core.database import get_db
from app.core.llm import llm_service
import json

router = APIRouter()

@router.post("/{project_id}/generate-summary")
async def generate_project_summary(project_id: int, type: str = "weekly", db: AsyncSession = Depends(get_db)):
    """
    Generate an AI-powered project summary (Weekly/Monthly).
    """
    result = await db.execute(
        select(Project)
        .filter(Project.id == project_id)
        .options(selectinload(Project.tasks))
    )
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks_summary = []
    for t in project.tasks:
        tasks_summary.append(f"- {t.title} (Status: {t.status}, Est: {t.original_duration}h)")

    prompt = f"""
    You are a Project Director. Generate a professional {type} project report for the following project:
    
    Title: {project.title}
    Description: {project.description}
    Current Status: {project.status}
    
    Task Progress:
    {chr(10).join(tasks_summary)}
    
    Include:
    1. Executive Summary
    2. Progress Benchmarking (against estimated hours)
    3. Potential Risks/Bottlenecks
    4. Next Cycle Objectives
    
    Format the response in clean Markdown with professional headers. Use a serious, data-driven tone typical of Bloomberg industrial analysis.
    """

    try:
        content = await llm_service.generate_text(prompt)
        return {
            "project_id": project_id,
            "report_type": type,
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
