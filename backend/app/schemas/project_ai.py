from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectGenerationRequest(BaseModel):
    description: str = Field(..., description="User's project idea or description / 用户项目构想或描述")
    industry: Optional[str] = Field(None, description="Industry or domain / 行业或领域")

class ProjectTaskGenerated(BaseModel):
    title: str = Field(..., description="Task title / 任务标题")
    description: str = Field(..., description="Task description / 任务描述")
    estimated_hours: float = Field(..., description="Estimated hours / 预计工时")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies (titles) / 任务依赖（标题）")

class ProjectMaterialGenerated(BaseModel):
    name: str = Field(..., description="Material name / 材料名称")
    category: str = Field(..., description="Category / 类别")
    quantity: float = Field(..., description="Quantity / 数量")
    unit: str = Field(..., description="Unit / 单位")
    unit_price: float = Field(..., description="Unit price / 单价")
    total_price: Optional[float] = Field(None, description="Total price / 总价")

class ProjectPlanGenerated(BaseModel):
    project_title: str = Field(..., description="Project title / 项目标题")
    summary: str = Field(..., description="Project summary / 项目摘要")
    tasks: List[ProjectTaskGenerated] = Field(..., description="List of tasks / 任务列表")
    materials: List[ProjectMaterialGenerated] = Field(default_factory=list, description="List of materials (MTO) / 材料清单")
    recommended_tech_stack: List[str] = Field(default_factory=list, description="Recommended technology stack /以内推荐技术栈")
