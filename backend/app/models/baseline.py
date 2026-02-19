from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ProjectBaseline(Base):
    """
    Stores a snapshot of the project at a specific point in time.
    Used for variance analysis and EVM.
    """
    __tablename__ = "project_baselines"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    name = Column(String, nullable=False) # e.g., "Initial Baseline", "Sep 2025 Update"
    description = Column(Text)
    baseline_type = Column(String, default="current") # original, current, what-if
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="baselines")
    task_baselines = relationship("TaskBaseline", back_populates="baseline", cascade="all, delete-orphan")

class TaskBaseline(Base):
    """
    Stores a snapshot of a task within a baseline.
    """
    __tablename__ = "task_baselines"

    id = Column(Integer, primary_key=True, index=True)
    baseline_id = Column(Integer, ForeignKey("project_baselines.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Snapshot Data (Baseline Planned)
    planned_start = Column(DateTime(timezone=True))
    planned_finish = Column(DateTime(timezone=True))
    duration = Column(Float)
    
    # CPM Snapshot
    early_start = Column(DateTime(timezone=True))
    early_finish = Column(DateTime(timezone=True))
    late_start = Column(DateTime(timezone=True))
    late_finish = Column(DateTime(timezone=True))
    total_float = Column(Float)
    
    # Execution Snapshot (at time of baseline)
    actual_start = Column(DateTime(timezone=True))
    actual_finish = Column(DateTime(timezone=True))
    status = Column(String)
    
    # Cost Data (for EVM)
    planned_cost = Column(Float, default=0.0) 
    
    # Relationships
    baseline = relationship("ProjectBaseline", back_populates="task_baselines")
    task = relationship("Task") 
