from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import Project, Blueprint, Task, Material
from app.core.database import get_db
import os
import uuid

router = APIRouter()

# Simple simulation of drawing analysis
# In a real app, this would use a Vision model or specialized CAD parsing
SIMULATED_MTO_RESULTS = [
    {"name": "Structural Steel H-Beam", "category": "Structural", "quantity": 45, "unit": "pcs", "unit_price": 450.0},
    {"name": "Concrete C30/37", "category": "Structural", "quantity": 120, "unit": "m3", "unit_price": 85.0},
    {"name": "Copper Wiring 2.5mm", "category": "Electrical", "quantity": 1500, "unit": "m", "unit_price": 2.5},
    {"name": "PVC Pipe 110mm", "category": "Plumbing", "quantity": 200, "unit": "m", "unit_price": 12.0}
]

@router.post("/projects/{project_id}/blueprints/upload")
async def upload_blueprint(
    project_id: int, 
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a blueprint (PDF/CAD) and trigger AI analysis.
    """
    # Create directory if not exists
    upload_dir = "uploads/blueprints"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    # Simulate AI analysis and extraction of MTO
    analysis_results = {
        "mto": SIMULATED_MTO_RESULTS,
        "summary": "Detected structural components and utility lines from architectural drawing."
    }
    
    blueprint = Blueprint(
        project_id=project_id,
        filename=file.filename,
        file_path=file_path,
        analysis_results=analysis_results
    )
    db.add(blueprint)
    
    # Optional: Automatically update materials in a 'From Blueprints' task
    blueprint_task = Task(
        project_id=project_id,
        title=f"Materials from Drawing: {file.filename}",
        description="Automatically extracted material list from uploaded blueprints.",
        status="todo"
    )
    db.add(blueprint_task)
    await db.flush()
    
    for item in SIMULATED_MTO_RESULTS:
        mat = Material(
            task_id=blueprint_task.id,
            name=item["name"],
            category=item["category"],
            quantity=item["quantity"],
            unit=item["unit"],
            unit_price=item["unit_price"],
            total_price=item["quantity"] * item["unit_price"]
        )
        db.add(mat)
        
    await db.commit()
    await db.refresh(blueprint)
    
    return {
        "message": "Blueprint uploaded and analyzed successfully",
        "blueprint_id": blueprint.id,
        "extracted_mto": SIMULATED_MTO_RESULTS
    }
