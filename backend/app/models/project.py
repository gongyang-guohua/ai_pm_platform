from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    industry = Column(String)
    summary = Column(Text)
    tech_stack = Column(JSON, default=list) # Recommended technology stack / 推荐技术栈
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="planning") # planning, active, completed, on_hold

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    blueprints = relationship("Blueprint", back_populates="project", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    baselines = relationship("ProjectBaseline", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("ProjectReport", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # WBS / Hierarchy (using ltree logic conceptually, stored as string path for now, or actual ltree if supported)
    # We will use a string method "1.1.2" for simplicity in valid standard SQL, 
    # but for Postgres specific ltree, we would use the Ltree type. 
    # To keep it compatible without heavy external deps immediately, we'll store specific WBS code.
    # However, for P6 recursion, 'path' is critical.
    # WBS / Hierarchy (using ltree logic conceptually, stored as string path for now, or actual ltree if supported)
    # We will use a string method "1.1.2" for simplicity in valid standard SQL, 
    # but for Postgres specific ltree, we would use the Ltree type. 
    # To keep it compatible without heavy external deps immediately, we'll store specific WBS code.
    # However, for P6 recursion, 'path' is critical.
    wbs_code = Column(String, index=True) # User defined WBS, e.g. "1.1"
    path = Column(String, index=True) # Materialized Path for hierarchy e.g. "root.1.5" (ltree compatible format)
    
    is_summary = Column(Boolean, default=False)
    outline_level = Column(Integer, default=1)
    
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    
    # Scheduling & Constraints
    priority = Column(String, default="Medium")
    status = Column(String, default="not_started") # not_started, in_progress, completed
    task_type = Column(String, default="task") # task, milestone, summary
    responsible_party = Column(String)
    
    # New Fields for Engineering/Deliverables
    is_deliverable = Column(Boolean, default=False)
    discipline = Column(String, default="General") # General, Design, Procurement, Construction, Commissioning
    
    # Calendar & Duration
    original_duration = Column(Float, default=0.0) # Planned duration in hours/days
    remaining_duration = Column(Float, default=0.0)

    planned_start = Column(DateTime(timezone=True))
    planned_end = Column(DateTime(timezone=True))
    
    # Constraints
    constraint_type = Column(String) # start_no_earlier_than, finish_no_later_than, must_finish_by, as_soon_as_possible
    constraint_date = Column(DateTime(timezone=True))
    
    # CPM Dates (Calculated)
    early_start = Column(DateTime(timezone=True))
    early_finish = Column(DateTime(timezone=True))
    late_start = Column(DateTime(timezone=True))
    late_finish = Column(DateTime(timezone=True))
    free_float = Column(Float, default=0.0)
    total_float = Column(Float, default=0.0)
    
    # Execution Dates (Actual)
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    
    # EVM (Earned Value Management)
    planned_value = Column(Float, default=0.0) # PV (Budgeted Cost of Work Scheduled)
    earned_value = Column(Float, default=0.0) # EV (Budgeted Cost of Work Performed)
    actual_cost = Column(Float, default=0.0) # AC (Actual Cost of Work Performed)
    budget_at_completion = Column(Float, default=0.0) # BAC
    estimate_at_completion = Column(Float, default=0.0) # EAC
    
    # Resources
    resource_ids = Column(JSON, default=list) # List of resource IDs
    
    # Relationships (Stored as JSON for simplicity, OR separate table)
    # For full P6, we need a separate table for TaskRelationships to support Lag, Type (SS, FS, etc).
    # We will define a separate table 'TaskRelationship' below and use logic there.
    
    project = relationship("Project", back_populates="tasks")
    relationships_pred = relationship("TaskRelationship", foreign_keys="TaskRelationship.successor_id", back_populates="successor", cascade="all, delete-orphan")
    relationships_succ = relationship("TaskRelationship", foreign_keys="TaskRelationship.predecessor_id", back_populates="predecessor", cascade="all, delete-orphan")
    materials = relationship("Material", back_populates="task", cascade="all, delete-orphan")

class TaskRelationship(Base):
    __tablename__ = "task_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    predecessor_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    successor_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Relationship Type: FS (Finish-to-Start), SS, FF, SF
    type = Column(String, default="FS", nullable=False) 
    lag = Column(Float, default=0.0) # Lag in hours/days
    
    predecessor = relationship("Task", foreign_keys=[predecessor_id], back_populates="relationships_succ")
    successor = relationship("Task", foreign_keys=[successor_id], back_populates="relationships_pred")

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    name = Column(String, index=True, nullable=False)
    category = Column(String) # e.g., Steel, Concrete, Software License / 材料类别
    quantity = Column(Float, default=0.0)
    unit = Column(String) # e.g., kg, m3, pcs / 单位
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)

    task = relationship("Task", back_populates="materials")



class Blueprint(Base):
    __tablename__ = "blueprints"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    analysis_results = Column(JSON) # Extracted MTO data / MTO 分析结果

    project = relationship("Project", back_populates="blueprints")

class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True) # Optional link to specific task
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    probability = Column(Float) # 0-1 or 1-5 scale
    impact = Column(Float)      # 1-5 scale
    mitigation_plan = Column(Text)
    status = Column(String, default="identified") # identified, monitored, mitigated, occurred, closed

    project = relationship("Project", back_populates="risks")
