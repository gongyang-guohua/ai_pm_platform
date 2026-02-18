from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.project import Risk, RiskCreate, RiskUpdate
from app.models.project import Risk as RiskModel
from app.core.database import get_db

router = APIRouter()

@router.post("/", response_model=Risk)
async def create_risk(risk_in: RiskCreate, project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Create a new project risk.
    """
    db_risk = RiskModel(
        project_id=project_id,
        **risk_in.model_dump()
    )
    db.add(db_risk)
    await db.commit()
    await db.refresh(db_risk)
    return db_risk

@router.get("/{project_id}", response_model=List[Risk])
async def list_risks(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    List all risks for a specific project.
    """
    result = await db.execute(select(RiskModel).filter(RiskModel.project_id == project_id))
    return result.scalars().all()

@router.put("/{risk_id}", response_model=Risk)
async def update_risk(risk_id: int, risk_in: RiskUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update a risk's details or status.
    """
    result = await db.execute(select(RiskModel).filter(RiskModel.id == risk_id))
    db_risk = result.scalars().first()
    if not db_risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    update_data = risk_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_risk, field, value)
    
    await db.commit()
    await db.refresh(db_risk)
    return db_risk

@router.delete("/{risk_id}")
async def delete_risk(risk_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a risk.
    """
    result = await db.execute(select(RiskModel).filter(RiskModel.id == risk_id))
    db_risk = result.scalars().first()
    if not db_risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    await db.delete(db_risk)
    await db.commit()
    return {"message": "Success"}
