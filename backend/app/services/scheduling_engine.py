from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import Task, TaskRelationship

class ProjectCalendar:
    """
    Handles working hours and days.
    Default: Mon-Fri, 08:00-12:00, 13:00-17:00 (8 hours/day).
    """
    def __init__(self):
        self.work_days = {0, 1, 2, 3, 4} # Mon-Fri
        self.work_start = time(8, 0)
        self.work_end = time(17, 0)
        self.lunch_start = time(12, 0)
        self.lunch_end = time(13, 0)
        self.hours_per_day = 8.0

    def is_working_time(self, dt: datetime) -> bool:
        if dt.weekday() not in self.work_days:
            return False
        t = dt.time()
        # Simple check: within start/end range?
        # Note: Lunch break logic can be complex. For CPM simplicity, we often treat 8-17 as contiguous 8h block 
        # or properly skip lunch. Let's do a robust check.
        if not (self.work_start <= t < self.work_end):
            return False
        if self.lunch_start <= t < self.lunch_end:
            return False
        return True

    def next_working_moment(self, dt: datetime) -> datetime:
        """Moves dt forward to the next valid working minute if it's currently non-working."""
        tz = dt.tzinfo
        for _ in range(5000): # Larger safety range for long weekends
            if self.is_working_time(dt):
                return dt
            
            # Optimization: Jump to relevant boundaries
            t = dt.time()
            if t >= self.work_end or dt.weekday() not in self.work_days:
                # Next day morning
                dt = datetime.combine(dt.date() + timedelta(days=1), self.work_start, tzinfo=tz)
            elif t < self.work_start:
                # Today morning
                dt = datetime.combine(dt.date(), self.work_start, tzinfo=tz)
            elif self.lunch_start <= t < self.lunch_end:
                # After lunch
                dt = datetime.combine(dt.date(), self.lunch_end, tzinfo=tz)
            else:
                # Fallback step
                dt += timedelta(minutes=1)
        return dt

    def prev_working_moment(self, dt: datetime) -> datetime:
        """Moves dt backward to the prev valid working minute."""
        tz = dt.tzinfo
        for _ in range(5000):
            if self.is_working_time(dt - timedelta(seconds=1)):
                 return dt
            
            t = dt.time()
            if t <= self.work_start or dt.weekday() not in self.work_days:
                # Prev day afternoon
                dt = datetime.combine(dt.date() - timedelta(days=1), self.work_end, tzinfo=tz)
            elif t > self.work_end:
                # Today afternoon
                dt = datetime.combine(dt.date(), self.work_end, tzinfo=tz)
            elif self.lunch_start < t <= self.lunch_end:
                # Before lunch
                dt = datetime.combine(dt.date(), self.lunch_start, tzinfo=tz)
            else:
                # Fallback step
                dt -= timedelta(minutes=1)
        return dt

    def add_working_duration(self, start: datetime, hours: float) -> datetime:
        """Adds working hours to a start date."""
        if hours == 0:
            return start
        if hours < 0:
            return self.subtract_working_duration(start, -hours)
        
        # Ensure we start from a working moment
        current = self.next_working_moment(start)
        remaining_minutes = int(hours * 60)
        
        while remaining_minutes > 0:
            # How many minutes left in current day?
            # Current time
            t = current.time()
            
            # Identify next break or end of day
            tz = current.tzinfo
            if t < self.lunch_start:
                next_break = datetime.combine(current.date(), self.lunch_start, tzinfo=tz)
            else:
                next_break = datetime.combine(current.date(), self.work_end, tzinfo=tz)
            
            minutes_available = (next_break - current).total_seconds() / 60
            
            if minutes_available <= 0:
                # Should have been advanced by next_working_moment usually, but robust check
                current = self.next_working_moment(current + timedelta(minutes=1))
                continue

            if remaining_minutes <= minutes_available:
                current += timedelta(minutes=remaining_minutes)
                remaining_minutes = 0
            else:
                current = next_break # Use up this block
                remaining_minutes -= int(minutes_available)
                current = self.next_working_moment(current) # Jump to next block
                
        return current

    def subtract_working_duration(self, end: datetime, hours: float) -> datetime:
        """Subtracts working hours from an end date."""
        if hours == 0:
            return end
        if hours < 0:
            return self.add_working_duration(end, -hours)

        # Ensure we start from a working moment
        current = self.prev_working_moment(end)
        remaining_minutes = int(hours * 60)
        
        while remaining_minutes > 0:
            t = current.time()
            
            # Define blocks: 08:00-12:00 and 13:00-17:00
            # If current is in afternoon block (13:00 < t <= 17:00) -> prev limit is 13:00
            # If current is in morning block (08:00 < t <= 12:00) -> prev limit is 08:00
            # Note: t=13:00 is valid start of afternoon block. t=12:00 is end of morning.
            
            # If t > 13:00? No, 13:00 is inclusive start?
            # 13:00 is working? Yes.
            # If t == 13:00. Block is done (0 duration available backwards).
            
            tz = current.tzinfo
            if t > self.lunch_end:
                # Afternoon block
                prev_limit = datetime.combine(current.date(), self.lunch_end, tzinfo=tz)
            elif t <= self.lunch_end and t > self.work_start: 
                # Morning block (handling constraint crossing)
                # If t <= 12:00 (lunch_start)?
                # If t is 13:00, we treat it as boundary.
                if t == self.lunch_end:
                     # At 13:00 boundary. 0 minutes available in this block going back.
                     # Move to 12:00
                     prev_limit = current # Dummy
                else:
                     prev_limit = datetime.combine(current.date(), self.work_start, tzinfo=tz)
            else:
                prev_limit = datetime.combine(current.date(), self.work_start, tzinfo=tz)

            minutes_available = (current - prev_limit).total_seconds() / 60
            
            if minutes_available <= 0:
               # Jump gap
               current = self.prev_working_moment(current - timedelta(seconds=1))
               continue
               
            if remaining_minutes <= minutes_available:
                current -= timedelta(minutes=remaining_minutes)
                remaining_minutes = 0
            else:
                current = prev_limit
                remaining_minutes -= int(minutes_available)
                current = self.prev_working_moment(current - timedelta(seconds=1)) # Jump gap

        return current

    def working_hours_between(self, start: datetime, end: datetime) -> float:
        """Calculates working hours between two dates."""
        if start >= end:
            return 0.0
        
        # Ensure we start from a valid working moment
        current = self.next_working_moment(start)
        if current >= end:
            return 0.0
            
        total_minutes = 0
        
        while current < end:
            t = current.time()
            tz = current.tzinfo
            
            # Current working block end
            if t < self.lunch_start:
                limit = datetime.combine(current.date(), self.lunch_start, tzinfo=tz)
            elif t < self.work_end:
                limit = datetime.combine(current.date(), self.work_end, tzinfo=tz)
            else:
                # Currently at or past work_end, move to next morning
                current = self.next_working_moment(current)
                continue
            
            # Constrain by absolute end
            limit = min(limit, end)
            
            minutes = (limit - current).total_seconds() / 60
            if minutes > 0:
                total_minutes += int(minutes)
                current = limit
            
            if current >= end:
                break
            
            # Move to next block or day
            # If current is at limit, we need to jump
            current = self.next_working_moment(current + timedelta(seconds=1))
            
        return total_minutes / 60.0


class SchedulingEngine:
    def __init__(self, session: AsyncSession, project_id: int):
        self.session = session
        self.project_id = project_id
        self.tasks: Dict[int, Task] = {}
        self.relationships: List[TaskRelationship] = []
        self.preds: Dict[int, List[TaskRelationship]] = {}
        self.succs: Dict[int, List[TaskRelationship]] = {}
        self.calendar = ProjectCalendar()

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
        self.preds = {}
        self.succs = {}
        for rel in self.relationships:
            if rel.successor_id not in self.preds:
                self.preds[rel.successor_id] = []
            self.preds[rel.successor_id].append(rel)
            
            if rel.predecessor_id not in self.succs:
                self.succs[rel.predecessor_id] = []
            self.succs[rel.predecessor_id].append(rel)

    def calculate_dates(self, project_start_date: datetime):
        """
        Performs the Critical Path Method (CPM) calculation.
        Supports FS, SS, FF, SF relationships and Lags.
        """
        if not self.tasks:
            return

        # Ensure project start is a working time
        project_start_date = self.calendar.next_working_moment(project_start_date)

        sorted_ids = self.topological_sort()
        
        # 1. Forward Pass: Calculate Early Start (ES) and Early Finish (EF)
        for t_id in sorted_ids:
            task = self.tasks[t_id]
            
            # Default Start: Project Start
            effective_es = project_start_date
            
            if t_id in self.preds:
                # Max of all predecessors constraints
                for rel in self.preds[t_id]:
                    if rel.predecessor_id not in self.tasks:
                        continue
                    pred = self.tasks[rel.predecessor_id]
                    
                    # Logic for different relationship types
                    if rel.type == 'FS':
                        # Succ.Start >= Pred.Finish + Lag
                        # Convert Lag (hours) to working time? Usually Lag is calendar days or working days.
                        # Assuming Lag is working hours for consistency.
                        base = self.calendar.add_working_duration(pred.early_finish, rel.lag)
                        constraint_date = base # ES
                    elif rel.type == 'SS':
                        # Succ.Start >= Pred.Start + Lag
                        base = self.calendar.add_working_duration(pred.early_start, rel.lag)
                        constraint_date = base # ES
                    elif rel.type == 'FF':
                        # Succ.Finish >= Pred.Finish + Lag
                        # Succ.Start = (Pred.Finish + Lag) - Duration
                        finish_constraint = self.calendar.add_working_duration(pred.early_finish, rel.lag)
                        constraint_date = self.calendar.subtract_working_duration(finish_constraint, task.original_duration)
                    elif rel.type == 'SF':
                        # Succ.Finish >= Pred.Start + Lag
                        # Succ.Start = (Pred.Start + Lag) - Duration
                        finish_constraint = self.calendar.add_working_duration(pred.early_start, rel.lag)
                        constraint_date = self.calendar.subtract_working_duration(finish_constraint, task.original_duration)
                    else:
                        constraint_date = project_start_date
                    
                    if constraint_date > effective_es:
                        effective_es = constraint_date
            
            # Application of "Start No Earlier Than" constraint
            if task.constraint_type == 'start_no_earlier_than' and task.constraint_date:
                cd = self.calendar.next_working_moment(task.constraint_date)
                if cd > effective_es:
                    effective_es = cd
            
            # Normalize ES to be a valid working moment (e.g. if 17:00, move to next day 08:00)
            task.early_start = self.calendar.next_working_moment(effective_es)
            duration = task.original_duration if task.original_duration is not None else 0.0
            task.early_finish = self.calendar.add_working_duration(task.early_start, duration)
        
        # Determine Project Finish Date
        finish_dates = [t.early_finish for t in self.tasks.values() if t.early_finish is not None]
        project_finish_date = max(finish_dates, default=project_start_date)
        
        # 2. Backward Pass: Calculate Late Finish (LF) and Late Start (LS)
        for t_id in reversed(sorted_ids):
            task = self.tasks[t_id]
            effective_lf = project_finish_date
            
            if t_id in self.succs:
                # Min of all successor constraints
                for rel in self.succs[t_id]:
                    if rel.successor_id not in self.tasks:
                        continue
                    succ = self.tasks[rel.successor_id]
                    
                    duration = task.original_duration if task.original_duration is not None else 0.0
                    if rel.type == 'FS':
                        # Pred.Finish <= Succ.Start - Lag
                        # LF = Succ.Start - Lag
                        constraint_date = self.calendar.subtract_working_duration(succ.late_start, rel.lag)
                    elif rel.type == 'SS':
                        # Pred.Start <= Succ.Start - Lag
                        # Pred.Finish = Limit(Pred.Start) + D = (Succ.Start - Lag) + D
                        start_limit = self.calendar.subtract_working_duration(succ.late_start, rel.lag)
                        constraint_date = self.calendar.add_working_duration(start_limit, duration)
                    elif rel.type == 'FF':
                        # Pred.Finish <= Succ.Finish - Lag
                        constraint_date = self.calendar.subtract_working_duration(succ.late_finish, rel.lag)
                    elif rel.type == 'SF':
                        # Pred.Start <= Succ.Finish - Lag
                        # Pred.Finish = (Succ.Finish - Lag) + D
                        start_limit = self.calendar.subtract_working_duration(succ.late_finish, rel.lag)
                        constraint_date = self.calendar.add_working_duration(start_limit, duration)
                    else:
                        constraint_date = project_finish_date
                    
                    if constraint_date < effective_lf:
                        effective_lf = constraint_date
            
            # Application of "Finish No Later Than" constraint
            if task.constraint_type == 'finish_no_later_than' and task.constraint_date:
                cd = self.calendar.prev_working_moment(task.constraint_date) # Should align to working time end
                if cd < effective_lf:
                    effective_lf = cd
            
            # Clamp LF to not be before ES? (Negative Float allowed if missed deadlines, but logic usually holds)
            
            task.late_finish = effective_lf
            # Calculate LS
            duration = task.original_duration if task.original_duration is not None else 0.0
            raw_ls = self.calendar.subtract_working_duration(task.late_finish, duration)
            # Normalize LS to valid start time (if landing on Fri 17:00, it effectively means Mon 08:00 start)
            task.late_start = self.calendar.next_working_moment(raw_ls)
            
            # 3. Float Calculation (working hours delta)
            # TF = Working hours between ES and LS.
            task.total_float = self.calendar.working_hours_between(task.early_start, task.late_start)

    def topological_sort(self) -> List[int]:
        # Kahn's algorithm
        in_degree = {t_id: 0 for t_id in self.tasks}
        for rel in self.relationships:
            if rel.successor_id in in_degree:
                in_degree[rel.successor_id] += 1
        
        queue = [t_id for t_id in self.tasks if in_degree[t_id] == 0]
        sorted_list = []
        
        while queue:
            u = queue.pop(0)
            sorted_list.append(u)
            
            if u in self.succs:
                for rel in self.succs[u]:
                    v = rel.successor_id
                    if v in in_degree: 
                        in_degree[v] -= 1
                        if in_degree[v] == 0:
                            queue.append(v)
        
        if len(sorted_list) != len(self.tasks):
             # Handle Cycle: Break loop or Raise Error?
             # For robustness, we might just process what we have or identify cycle.
             # Returning partial list often bad.
             # Identify tasks involved in cycle?
             # Simple fallback: Return standard list but warn.
             # Raising error stops everything. 
             raise ValueError("Cycle detected in project schedule")
            
        return sorted_list

    async def save_dates(self):
        for task in self.tasks.values():
            self.session.add(task)

