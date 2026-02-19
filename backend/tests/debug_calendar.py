
import sys
import os
from datetime import datetime, time, timedelta

# Mock Calendar to avoid imports for debugging logic
class ProjectCalendar:
    def __init__(self):
        self.work_days = {0, 1, 2, 3, 4} # Mon-Fri
        self.work_start = time(8, 0)
        self.work_end = time(17, 0)
        self.lunch_start = time(12, 0)
        self.lunch_end = time(13, 0)

    def is_working_time(self, dt: datetime) -> bool:
        if dt.weekday() not in self.work_days:
            return False
        t = dt.time()
        if not (self.work_start <= t < self.work_end):
            return False
        if self.lunch_start <= t < self.lunch_end:
            return False
        return True

    def prev_working_moment(self, dt: datetime) -> datetime:
        for _ in range(100):
            if self.is_working_time(dt - timedelta(seconds=1)):
                 return dt
            dt -= timedelta(minutes=1)
            if dt.time() <= self.work_start:
                dt = datetime.combine(dt.date() - timedelta(days=1), self.work_end)
            elif dt.weekday() not in self.work_days:
                dt = datetime.combine(dt.date() - timedelta(days=1), self.work_end)
            elif self.lunch_start < dt.time() <= self.lunch_end:
                dt = datetime.combine(dt.date(), self.lunch_start)
        return dt

    def subtract_working_duration(self, end: datetime, hours: float) -> datetime:
        if hours == 0:
            return end
        
        print(f"Subtracting {hours}h from {end}")
        current = self.prev_working_moment(end)
        print(f"Start Working Moment: {current}")
        remaining_minutes = int(hours * 60)
        
        while remaining_minutes > 0:
            t = current.time()
            if t > self.lunch_end:
                prev_limit = datetime.combine(current.date(), self.lunch_end)
            elif t <= self.lunch_end and t > self.work_start: 
                if t == self.lunch_end:
                     prev_limit = current 
                else:
                     prev_limit = datetime.combine(current.date(), self.work_start)
            else:
                prev_limit = datetime.combine(current.date(), self.work_start)

            minutes_available = (current - prev_limit).total_seconds() / 60
            print(f"Current: {current}, Limit: {prev_limit}, Avail: {minutes_available}, Rem: {remaining_minutes}")

            if minutes_available <= 0:
               current = self.prev_working_moment(current - timedelta(seconds=1))
               print(f"Jumped gap (0 avail) to {current}")
               continue
               
            if remaining_minutes <= minutes_available:
                current -= timedelta(minutes=remaining_minutes)
                remaining_minutes = 0
                print(f"Finished. Result: {current}")
            else:
                remaining_minutes -= int(minutes_available)
                current = prev_limit
                print(f"Consumed block. Current: {current}. New Rem: {remaining_minutes}")
                current = self.prev_working_moment(current - timedelta(seconds=1))
                print(f"Jumped gap to {current}")

        return current

cal = ProjectCalendar()
res = cal.subtract_working_duration(datetime(2024, 1, 5, 8, 0), 24)
print(f"Final Result: {res}")
