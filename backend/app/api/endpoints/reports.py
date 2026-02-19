from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.models.project import Project, Task
from app.models.report import ProjectReport, ReportStatus
from app.core.database import get_db
from app.services.ai_service import deepflow_agent

router = APIRouter()

async def generate_report_background(report_id: int, project_id: int, report_type: str, language: str, db: AsyncSession):
    """
    Background task to generate report and update database.
    Note: We need a new DB session here because the request session will be closed.
    Actually, FastAPI BackgroundTasks can accept async functions, but passing the original dependency db session
    might be risky if the response closes it. Best practice is to create a new session or be careful.
    For simplicity with async session dependency, we might need a context manager or passing the session factory.
    Wait, `db` dependency is closed after request. We must create a NEW session.
    """
    # Since we can't easily inject a new session factory here without circular imports or structural changes,
    # we will try to use the `app.core.database.async_session` maker if available, or just re-import.
    from app.core.database import async_session
    
    async with async_session() as session:
        try:
            # 1. Fetch Project Data
            result = await session.execute(
                select(Project)
                .filter(Project.id == project_id)
                .options(selectinload(Project.tasks))
            )
            project = result.scalars().first()
            if not project:
                # Should not happen if API checked validity, but safety first
                return

            # 2. Update status to PROCESSING
            result = await session.execute(select(ProjectReport).filter(ProjectReport.id == report_id))
            report = result.scalars().first()
            if report:
                report.status = ReportStatus.PROCESSING
                await session.commit()

            # 3. Generate Content
            # Use DeepFlow Multi-Agent System with a timeout
            content = await asyncio.wait_for(
                deepflow_agent.generate_deepflow_report(project, report_type, language),
                timeout=600.0
            )

            # 4. Update Report with Content
            # Re-fetch to avoid stale state issues (though unlikely in this flow)
            result = await session.execute(select(ProjectReport).filter(ProjectReport.id == report_id))
            report = result.scalars().first()
            if report:
                report.content = content
                report.status = ReportStatus.COMPLETED
                await session.commit()
                
        except asyncio.TimeoutError:
            print(f"Report {report_id} timed out.")
            result = await session.execute(select(ProjectReport).filter(ProjectReport.id == report_id))
            report = result.scalars().first()
            if report:
                report.status = ReportStatus.FAILED
                report.error_message = "Generation timed out after 10 minutes."
                await session.commit()
        except Exception as e:
            print(f"Report {report_id} failed: {e}")
            result = await session.execute(select(ProjectReport).filter(ProjectReport.id == report_id))
            report = result.scalars().first()
            if report:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                await session.commit()

@router.post("/{project_id}/generate-summary")
async def generate_project_summary(
    project_id: int, 
    background_tasks: BackgroundTasks,
    type: str = "weekly", 
    language: str = "en",
    db: AsyncSession = Depends(get_db)
):
    """
    Start background task to generate project summary.
    Returns 202 Accepted with report_id.
    """
    # Verify project exists
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create Report Record
    new_report = ProjectReport(
        project_id=project_id,
        report_type=type,
        language=language,
        status=ReportStatus.PENDING
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)

    # Launch Background Task
    background_tasks.add_task(generate_report_background, new_report.id, project_id, type, language, db)

    return {
        "message": "Report generation started",
        "report_id": new_report.id,
        "status": "pending"
    }

@router.get("/{project_id}/reports")
async def get_project_reports(
    project_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """
    Get all reports for a project, sorted by newest first.
    """
    result = await db.execute(
        select(ProjectReport)
        .filter(ProjectReport.project_id == project_id)
        .order_by(desc(ProjectReport.created_at))
    )
    reports = result.scalars().all()
    return reports
