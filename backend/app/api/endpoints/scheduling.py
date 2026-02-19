from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.project import Project
from app.services.scheduling_engine import SchedulingEngine
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.post("/{project_id}/schedule", status_code=status.HTTP_200_OK)
async def run_schedule(
    project_id: int,
    data_date: Optional[datetime] = Body(None, embed=True),
    db: AsyncSession = Depends(deps.get_db),
):
    """
    Run Enhanced P6-style CPM Scheduling (Supports FS, SS, FF, SF, Lag).
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Initialize Engine
    engine = SchedulingEngine(db, project_id)
    await engine.load_data()
    
    try:
        # Use provided Data Date or current system time (UTC)
        from datetime import timezone
        start_date = data_date or datetime.now(timezone.utc)
        
        engine.calculate_dates(start_date)
        await engine.save_dates()
        await db.commit()
        
        return {
            "message": "Schedule calculation completed successfully",
            "data_date": start_date,
            "project_id": project_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
