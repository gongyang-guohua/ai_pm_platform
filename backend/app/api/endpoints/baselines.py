from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.services.baseline_service import BaselineService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class BaselineCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    baseline_type: str = "current"

class BaselineResponseSchema(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    baseline_type: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/{project_id}/baselines", response_model=BaselineResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_project_baseline(
    project_id: int,
    data: BaselineCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new baseline snapshot for a project.
    """
    service = BaselineService(db)
    try:
        baseline = await service.create_baseline(
            project_id=project_id,
            name=data.name,
            description=data.description,
            baseline_type=data.baseline_type
        )
        return baseline
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create baseline: {str(e)}")

@router.get("/{project_id}/baselines", response_model=List[BaselineResponseSchema])
async def list_project_baselines(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all baselines for a project.
    """
    service = BaselineService(db)
    return await service.get_project_baselines(project_id)

@router.get("/{project_id}/baselines/{baseline_id}/compare")
async def compare_baseline(
    project_id: int,
    baseline_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare current project schedule with a specific baseline.
    """
    service = BaselineService(db)
    try:
        comparison = await service.compare_baseline(project_id, baseline_id)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
