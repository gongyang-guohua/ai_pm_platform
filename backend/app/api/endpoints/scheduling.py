from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.models.project import Project
from app.services.scheduling_engine import SchedulingEngine
from datetime import datetime

router = APIRouter()

@router.post("/{project_id}/schedule", status_code=status.HTTP_200_OK)
async def run_schedule(
    project_id: int,
    db: AsyncSession = Depends(deps.get_db),
    # current_user: User = Depends(deps.get_current_active_user) # Add auth if needed
):
    """
    Run CPM Scheduling (Forward/Backward Pass) for the project.
    """
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Initialize Engine
    engine = SchedulingEngine(db, project_id)
    await engine.load_data()
    
    try:
        # Determine Project Start Date
        # Use existing start date or today
        # In P6, "Data Date" is crucial. We'll assume Data Date = Today or Project Start.
        start_date = datetime.now()
        # TODO: Get Data Date from request body or project settings
        
        engine.calculate_dates(start_date)
        await engine.save_dates()
        await db.commit()
        
        return {"message": "Schedule calculation completed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
