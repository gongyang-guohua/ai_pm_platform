from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class RiskBase(BaseModel):
    title: str
    description: Optional[str] = None
    probability: float = 0.0 # 0.0 to 1.0 or 1-5
    impact: float = 0.0      # 1-5
    mitigation_plan: Optional[str] = None
    status: str = "identified"
    task_id: Optional[int] = None

class RiskCreate(RiskBase):
    pass

class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    probability: Optional[float] = None
    impact: Optional[float] = None
    mitigation_plan: Optional[str] = None
    status: Optional[str] = None
    task_id: Optional[int] = None

class Risk(RiskBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    name: str
    category: Optional[str] = None
    quantity: float = 0.0
    unit: Optional[str] = None
    unit_price: float = 0.0
    total_price: float = 0.0

class MaterialCreate(MaterialBase):
    pass

class Material(MaterialBase):
    id: int
    task_id: int

    class Config:
        from_attributes = True

class Dependency(BaseModel):
    target_id: int
    relation: str = "FS" # FS, SS, FF, SF
    lag: float = 0.0

class TaskBase(BaseModel):
    title: str
    wbs_code: Optional[str] = None
    description: Optional[str] = None
    priority: str = "Medium"

    priority: str = "Medium"
    estimated_hours: Optional[float] = None
    original_duration: Optional[float] = None
    status: str = "not_started"
    task_type: str = "task" # task, milestone
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    responsible_party: Optional[str] = None
    helper_party: Optional[str] = None
    dependencies: List[Dependency | str] = []
    notes: Optional[str] = None
    is_summary: bool = False
    outline_level: int = 1
    # Engineering Fields
    discipline: Optional[str] = None
    is_deliverable: Optional[bool] = False

class TaskCreate(TaskBase):
    project_id: int
    materials: List[MaterialCreate] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    wbs_code: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    task_type: Optional[str] = None
    estimated_hours: Optional[float] = None
    original_duration: Optional[float] = None
    actual_cost: Optional[float] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    responsible_party: Optional[str] = None
    helper_party: Optional[str] = None
    dependencies: Optional[List[Dependency]] = None
    notes: Optional[str] = None

class Task(TaskBase):
    id: int
    project_id: int
    actual_cost: Optional[float] = None
    materials: List[Material] = []

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    industry: Optional[str] = None
    summary: Optional[str] = None
    tech_stack: List[str] = []
    status: str = "planning"

class ProjectCreate(ProjectBase):
    tasks: List[TaskCreate] = []
    materials: List[MaterialCreate] = []

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    tech_stack: Optional[List[str]] = None

class Project(ProjectBase):
    id: int
    created_at: datetime
    tasks: List[Task] = []
    risks: List[Risk] = []
    # Project-level materials can be managed through a default task or separately
    # For now, we keep them linked to tasks in the DB but allow flat input.

    class Config:
        from_attributes = True
