from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.schemas.project_ai import ProjectGenerationRequest, ProjectPlanGenerated
from app.schemas.project import ProjectCreate, ProjectUpdate, Project as ProjectSchema
from app.models.project import Project, Task, Material, Risk
from app.core.database import get_db
from app.core.llm import llm_service
import json
import asyncio

router = APIRouter()

@router.post("/generate-plan", response_model=ProjectPlanGenerated)
async def generate_project_plan(request: ProjectGenerationRequest):
    """
    Generate a project plan using AI based on the user's description.
    基于用户的描述，使用 AI 生成项目计划。
    """
    
    prompt = f"""
    You are an expert Project Manager and Engineer. Create a comprehensive project plan for the following request:
    
    Project Description: {request.description}
    Industry: {request.industry or "General"}
    
    The plan must include tasks, a Material Take-Off (MTO), and initial cost estimations.
    
    Return the response in STRICT JSON format matching the following structure. Do not include any markdown formatting.
    
    {{
        "project_title": "Detailed Project Title",
        "summary": "Executive summary including scale and overall objective",
        "tasks": [
            {{
                "title": "Task Name",
                "description": "Clear step-by-step detail",
                "estimated_hours": 12.5,
                "dependencies": ["Task Name 1"]
            }}
        ],
        "materials": [
            {{
                "name": "Material/Asset Name",
                "category": "e.g., Structural, Electrical, Software",
                "quantity": 100,
                "unit": "kg/m/pcs",
                "unit_price": 50.0
            }}
        ],
        "recommended_tech_stack": ["Tool 1", "Tool 2"]
    }}
    """
    
    try:
        # Retry logic for LLM stability
        max_retries = 3
        import re
        
        for attempt in range(max_retries):
            try:
                print(f"DEBUG: Generating project plan, attempt {attempt+1}")
                response_text = await llm_service.generate_text(prompt)
                
                # Check for explicit error messages from LLM service
                # Check for explicit error messages from LLM service
                if response_text.startswith("Error:") or response_text.startswith("**System Notice:"):
                    print(f"DEBUG: LLM returned error/notice: {response_text[:100]}...")
                    # Immediately return fallback plan on System Notice (Region Lock/404)
                    print("WARN: Returning fallback plan due to AI Service Error/Notice.")
                    return {
                        "project_title": request.description[:50] or "New Project",
                        "summary": "AI generation failed (Region/Model Unavailable). Please add tasks manually.",
                        "tasks": [
                            {
                                "title": "Project Initialization",
                                "description": "AI generation encountered an error. Please define tasks manually.",
                                "estimated_hours": 0,
                                "dependencies": []
                            }
                        ],
                        "materials": [],
                        "recommended_tech_stack": []
                    }

                # Improved JSON extraction using regex
                # Look for { ... } structure, potentially multiline
                json_match = re.search(r"\{[\s\S]*\}", response_text)
                if not json_match:
                     print(f"DEBUG: No JSON found in response: {response_text[:200]}...")
                     if attempt < max_retries - 1:
                         await asyncio.sleep(1)
                         continue
                     else:
                         raise ValueError("Failed to parse valid JSON from AI response")
                
                clean_text = json_match.group(0)
                
                # Parse JSON
                try:
                    plan_data = json.loads(clean_text)
                except json.JSONDecodeError as je:
                    print(f"DEBUG: JSON extraction failed: {je}")
                    # Fallback cleanup
                    clean_text = response_text.replace("```json", "").replace("```", "").strip()
                    plan_data = json.loads(clean_text)

                # Add calculated total prices to materials
                if "materials" in plan_data:
                    for mat in plan_data["materials"]:
                        mat["total_price"] = mat.get("quantity", 0) * mat.get("unit_price", 0)
                
                # Validate with schema before returning catch Pydantic errors here
                try:
                    ProjectPlanGenerated.model_validate(plan_data)
                except Exception as ve:
                    print(f"DEBUG: Pydantic Validation Error: {ve}")
                    # If strictly required fields are missing, let's try to patch them or fail retry
                    if attempt < max_retries - 1:
                        print("DEBUG: Retrying due to validation error...")
                        await asyncio.sleep(1)
                        continue
                    raise ve

                return plan_data
            except Exception as e:
                print(f"DEBUG: Error in attempt {attempt+1}: {str(e)}")
                if attempt == max_retries - 1:
                    # If all retries fail, returning a default empty plan to avoid 500 crash
                    # This allows the UI to show *something* rather than an error page
                    print("CRITICAL: All attempts failed. Returning fallback plan.")
                    # Fallback plan matches ProjectPlanGenerated schema
                    fallback_plan = {
                        "project_title": request.description[:50] or "New Project",
                        "summary": "AI generation failed. Please add tasks manually.",
                        "tasks": [
                            {
                                "title": "Project Initialization",
                                "description": "AI generation encountered an error. Please define tasks manually.",
                                "estimated_hours": 0,
                                "dependencies": []
                            }
                        ],
                        "materials": [],
                        "recommended_tech_stack": []
                    }
                    return fallback_plan
                await asyncio.sleep(1)

    except Exception as e:
        import traceback
        error_msg = "".join(traceback.format_exception(None, e, e.__traceback__))
        print(f"CRITICAL: Generate project plan failed: {str(e)}")
        print(error_msg)
        
        # NUCLEAR FALLBACK: Return default plan no matter what happened
        return {
            "project_title": request.description[:50] or "New Project (Fallback)",
            "summary": "System encountered an error during generation. Manual entry required.",
            "tasks": [
                {
                    "title": "Manual Planning Required",
                    "description": f"AI Generation Failed: {str(e)[:100]}...",
                    "estimated_hours": 0,
                    "dependencies": []
                }
            ],
            "materials": [],
            "recommended_tech_stack": []
        }

@router.post("/", response_model=ProjectSchema)
async def create_project(project_in: ProjectCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new project with tasks and materials.
    """
    db_project = Project(
        title=project_in.title,
        description=project_in.description,
        industry=project_in.industry,
        summary=project_in.summary,
        tech_stack=project_in.tech_stack,
        status=project_in.status
    )
    db.add(db_project)
    await db.flush()

    # Create a default 'Project Inventory' task if there are materials but no tasks,
    # or just link materials to the first task.
    
    # First, create all tasks
    task_map = {} # title -> db_task
    for task_in in project_in.tasks:
        db_task = Task(
            project_id=db_project.id,
            title=task_in.title,
            description=task_in.description,
            original_duration=task_in.original_duration,
            status=task_in.status,
            # We will process dependencies in a second pass to ensure we have IDs for all tasks 
        )
        db.add(db_task)
        await db.flush()
        task_map[db_task.title] = db_task

    # Second pass: Resolve dependencies
    for task_in in project_in.tasks:
        db_task = task_map.get(task_in.title)
        if not db_task:
            continue
            
        # Create TaskRelationship objects
        # Note: task_in.dependencies is a list of strings (titles) or Dependency objects
        from app.models.project import TaskRelationship
        
        for dep in task_in.dependencies:
            pred_id = None
            rel_type = "FS"
            lag = 0.0
            
            if isinstance(dep, str):
                 target = task_map.get(dep)
                 if target:
                     pred_id = target.id
            elif isinstance(dep, dict):
                 # If it's a dict (from Pydantic dump or JSON)
                 target_id = dep.get("target_id")
                 if target_id:
                     pred_id = target_id
                 # If we have title based ref in dict? unlikely for now
                 rel_type = dep.get("relation", "FS")
                 lag = dep.get("lag", 0.0)
            else:
                 # Pydantic object
                 target_id = getattr(dep, "target_id", None)
                 if target_id:
                     pred_id = target_id
                 rel_type = getattr(dep, "relation", "FS")
                 lag = getattr(dep, "lag", 0.0)
            
            if pred_id:
                tr = TaskRelationship(
                    project_id=db_project.id,
                    predecessor_id=pred_id,
                    successor_id=db_task.id,
                    type=rel_type,
                    lag=lag
                )
                db.add(tr)

    # Create a 'General Logistics' task if we have materials but want them grouped separately
    if project_in.materials:
        logistics_task = Task(
            project_id=db_project.id,
            title="General Logistics & Procurement",
            description="Acquisition and management of project materials",
            estimated_hours=0.0,
            status="todo"
        )
        db.add(logistics_task)
        await db.flush()
        
        for mat_in in project_in.materials:
            db_mat = Material(
                task_id=logistics_task.id,
                name=mat_in.name,
                category=mat_in.category,
                quantity=mat_in.quantity,
                unit=mat_in.unit,
                unit_price=mat_in.unit_price,
                total_price=mat_in.total_price
            )
            db.add(db_mat)

    await db.commit()
    
    stmt = (
        select(Project)
        .where(Project.id == db_project.id)
        .options(
            selectinload(Project.tasks).selectinload(Task.materials),
            selectinload(Project.tasks).selectinload(Task.relationships_pred),
            selectinload(Project.risks),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one()
    
@router.get("/{project_id}", response_model=ProjectSchema)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a specific project by ID.
    """
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.tasks).selectinload(Task.materials),
            selectinload(Project.tasks).selectinload(Task.relationships_pred),
            selectinload(Project.risks),
        )
    )
    result = await db.execute(stmt)
    project = result.unique().scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/", response_model=List[ProjectSchema])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """
    List all projects.
    """
    stmt = select(Project).options(
        selectinload(Project.tasks).selectinload(Task.materials),
        selectinload(Project.tasks).selectinload(Task.relationships_pred),
        selectinload(Project.risks),
    )
    result = await db.execute(stmt)
    return result.unique().scalars().all()

@router.put("/{project_id}", response_model=ProjectSchema)
async def update_project(project_id: int, project_in: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    """
    Update a project.
    """
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    await db.commit()
    
    # Reload with relationships
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.tasks).selectinload(Task.materials),
            selectinload(Project.tasks).selectinload(Task.relationships_pred),
            selectinload(Project.risks),
        )
    )
    result = await db.execute(stmt)
    return result.unique().scalar_one()

@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete a project and all its related data.
    """
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    return {"message": "Success"}
