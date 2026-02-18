from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Task, TaskRelationship

class SchedulingEngine:
    def __init__(self, session: AsyncSession, project_id: int):
        self.session = session
        self.project_id = project_id
        self.tasks: Dict[int, Task] = {}
        self.relationships: List[TaskRelationship] = []
        self.preds: Dict[int, List[TaskRelationship]] = {}
        self.succs: Dict[int, List[TaskRelationship]] = {}

    async def load_data(self):
        # Load tasks
        result = await self.session.execute(
            select(Task).where(Task.project_id == self.project_id)
        )
        tasks_list = result.scalars().all()
        self.tasks = {t.id: t for t in tasks_list}
        
        # Load relationships
        result = await self.session.execute(
            select(TaskRelationship).where(TaskRelationship.project_id == self.project_id)
        )
        self.relationships = result.scalars().all()
        
        # Build graph
        for rel in self.relationships:
            if rel.successor_id not in self.preds:
                self.preds[rel.successor_id] = []
            self.preds[rel.successor_id].append(rel)
            
            if rel.predecessor_id not in self.succs:
                self.succs[rel.predecessor_id] = []
            self.succs[rel.predecessor_id].append(rel)

    def calculate_dates(self, project_start_date: datetime):
        # Topological sort or simple iterative approach (since DAG is required)
        # For simplicity and handling dependencies, we'll use a graph traversal
        
        # 1. Forward Pass
        # Initialize verified tasks set
        processed = set()
        queue = []
        
        # Find start nodes (no predecessors)
        for t_id, task in self.tasks.items():
            if t_id not in self.preds:
                task.early_start = project_start_date
                task.early_finish = self.add_duration(task.early_start, task.original_duration)
                processed.add(t_id)
                project_start_date = task.early_start # Keep reference
        
        # We need a proper topological sort or iterative pass to handle dependencies
        # Simple approach: Loop until no changes (inefficient) or standard topo sort.
        # Let's do topological sort first to check for loops.
        
        sorted_ids = self.topological_sort()
        
        # Forward Pass
        for t_id in sorted_ids:
            task = self.tasks[t_id]
            
            # Determine ES based on predecessors
            max_ef_plus_lag = project_start_date
            
            if t_id in self.preds:
                for rel in self.preds[t_id]:
                    pred_task = self.tasks[rel.predecessor_id]
                    # Logic for FS (Finish-to-Start)
                    if rel.type == 'FS':
                        date = self.add_duration(pred_task.early_finish, rel.lag)
                    elif rel.type == 'SS':
                        date = self.add_duration(pred_task.early_start, rel.lag)
                        # TODO: Add logic for FF, SF
                    else:
                        date = pred_task.early_finish # Fallback
                    
                    if date > max_ef_plus_lag:
                        max_ef_plus_lag = date
            
            # Constraints
            if task.constraint_type == 'start_no_earlier_than' and task.constraint_date:
                if task.constraint_date > max_ef_plus_lag:
                    max_ef_plus_lag = task.constraint_date
            
            task.early_start = max_ef_plus_lag
            task.early_finish = self.add_duration(task.early_start, task.original_duration)
        
        # 2. Backward Pass
        # Calculate Project Finish Date
        project_finish_date = project_start_date
        for task in self.tasks.values():
            if task.early_finish > project_finish_date:
                project_finish_date = task.early_finish
        
        reversed_ids = sorted_ids[::-1]
        
        for t_id in reversed_ids:
            task = self.tasks[t_id]
            
            # Determine LF based on successors
            min_ls_minus_lag = project_finish_date
            
            if t_id in self.succs:
                has_successors = True
                for rel in self.succs[t_id]:
                    succ_task = self.tasks[rel.successor_id]
                    
                    if rel.type == 'FS':
                        date = self.subtract_duration(succ_task.late_start, rel.lag)
                    elif rel.type == 'SS':
                         # Logic for SS in backward pass affects Late Start mainly
                         # Here simplifying for FS
                         date = succ_task.late_start # Placeholder
                    else:
                        date = succ_task.late_start
                    
                    if date < min_ls_minus_lag:
                        min_ls_minus_lag = date
            else:
                # No successors, LF = Project Finish
                min_ls_minus_lag = project_finish_date
            
            # Constraints
            if task.constraint_type == 'finish_no_later_than' and task.constraint_date:
                if task.constraint_date < min_ls_minus_lag:
                    min_ls_minus_lag = task.constraint_date
            
            task.late_finish = min_ls_minus_lag
            task.late_start = self.subtract_duration(task.late_finish, task.original_duration)
            
            # 3. Float
            task.total_float = (task.late_start - task.early_start).total_seconds() / 3600.0 # Hours
            if task.total_float < 0:
                # Negative float?
                pass

    def add_duration(self, start: datetime, duration_hours: float) -> datetime:
        # TODO: Use Calendar (working hours)
        # Checking for None
        if not start:
            return datetime.now()
        if not duration_hours:
            return start
        return start + timedelta(hours=duration_hours)

    def subtract_duration(self, end: datetime, duration_hours: float) -> datetime:
         # TODO: Use Calendar
        if not end:
            return datetime.now()
        if not duration_hours:
            return end
        return end - timedelta(hours=duration_hours)

    def topological_sort(self) -> List[int]:
        # Kahn's algorithm
        in_degree = {t_id: 0 for t_id in self.tasks}
        for rel in self.relationships:
            in_degree[rel.successor_id] += 1
        
        queue = [t_id for t_id in self.tasks if in_degree[t_id] == 0]
        sorted_list = []
        
        while queue:
            u = queue.pop(0)
            sorted_list.append(u)
            
            if u in self.succs:
                for rel in self.succs[u]:
                    v = rel.successor_id
                    if v in in_degree: # Added check
                        in_degree[v] -= 1
                        if in_degree[v] == 0:
                            queue.append(v)
        
        if len(sorted_list) != len(self.tasks):
            raise ValueError("Cycle detected in project schedule")
            
        return sorted_list

    async def save_dates(self):
        # Objects are already tracked by session, just need commit in caller
        # But explicit add might be safe
        for task in self.tasks.values():
            self.session.add(task)
