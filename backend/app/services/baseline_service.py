from datetime import datetime, timezone
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.project import Project, Task
from app.models.baseline import ProjectBaseline, TaskBaseline

class BaselineService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_baseline(self, project_id: int, name: str, description: Optional[str] = None, baseline_type: str = "current") -> ProjectBaseline:
        """
        Creates a snapshot of the project tasks as a new baseline.
        """
        # 1. Fetch Project with Tasks
        result = await self.session.execute(
            select(Project)
            .filter(Project.id == project_id)
            .options(selectinload(Project.tasks))
        )
        project = result.scalars().first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 2. Create ProjectBaseline record
        baseline = ProjectBaseline(
            project_id=project_id,
            name=name,
            description=description,
            baseline_type=baseline_type,
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(baseline)
        await self.session.flush() # Get baseline.id

        # 3. Create TaskBaseline records for all tasks
        for task in project.tasks:
            task_baseline = TaskBaseline(
                baseline_id=baseline.id,
                task_id=task.id,
                planned_start=task.early_start or task.planned_start,
                planned_finish=task.early_finish or task.planned_end,
                duration=task.original_duration,
                early_start=task.early_start,
                early_finish=task.early_finish,
                late_start=task.late_start,
                late_finish=task.late_finish,
                total_float=task.total_float,
                actual_start=task.actual_start,
                actual_finish=task.actual_end,
                status=task.status,
                planned_cost=task.planned_value
            )
            self.session.add(task_baseline)

        await self.session.commit()
        await self.session.refresh(baseline)
        return baseline

    async def get_project_baselines(self, project_id: int) -> List[ProjectBaseline]:
        result = await self.session.execute(
            select(ProjectBaseline)
            .filter(ProjectBaseline.project_id == project_id)
            .order_by(ProjectBaseline.created_at.desc())
        )
        return result.scalars().all()

    async def compare_baseline(self, project_id: int, baseline_id: int) -> List[Dict]:
        """
        Compares current project tasks with a specific baseline.
        Returns variance data.
        """
        # 1. Fetch current tasks
        result = await self.session.execute(
            select(Task).filter(Task.project_id == project_id)
        )
        current_tasks = {t.id: t for t in result.scalars().all()}

        # 2. Fetch baseline tasks
        result = await self.session.execute(
            select(TaskBaseline).filter(TaskBaseline.baseline_id == baseline_id)
        )
        baseline_tasks = {tb.task_id: tb for tb in result.scalars().all()}

        # 3. Calculate Variances
        comparison = []
        for t_id, task in current_tasks.items():
            bt = baseline_tasks.get(t_id)
            
            variance = {
                "task_id": t_id,
                "task_title": task.title,
                "variance_start_hours": 0.0,
                "variance_finish_hours": 0.0,
                "variance_duration_hours": 0.0,
                "status_changed": False
            }

            if bt:
                # Calculate start delay (in hours, approximate using total_seconds)
                if task.early_start and bt.early_start:
                    variance["variance_start_hours"] = (task.early_start - bt.early_start).total_seconds() / 3600.0
                
                # Calculate finish delay
                if task.early_finish and bt.early_finish:
                    variance["variance_finish_hours"] = (task.early_finish - bt.early_finish).total_seconds() / 3600.0
                
                variance["variance_duration_hours"] = (task.original_duration or 0) - (bt.duration or 0)
                variance["status_changed"] = task.status != bt.status
                
                # Snapshot data for display
                variance["baseline_start"] = bt.early_start
                variance["baseline_finish"] = bt.early_finish
                variance["current_start"] = task.early_start
                variance["current_finish"] = task.early_finish

            comparison.append(variance)

        return comparison
