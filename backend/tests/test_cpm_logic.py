import unittest
from datetime import datetime, timedelta
from app.services.scheduling_engine import SchedulingEngine
from app.models.project import Task, TaskRelationship

class TestCPM(unittest.TestCase):
    def test_cpm_basic(self):
        # Create a dummy engine
        engine = SchedulingEngine(None, 1)
        
        # Create Tasks
        # A (5d) -> B (3d) -> D (2d)
        # A (5d) -> C (4d) -> D (2d)
        
        t1 = Task(id=1, original_duration=5, constraint_type=None) # A
        t2 = Task(id=2, original_duration=3, constraint_type=None) # B
        t3 = Task(id=3, original_duration=4, constraint_type=None) # C
        t4 = Task(id=4, original_duration=2, constraint_type=None) # D
        
        engine.tasks = {1: t1, 2: t2, 3: t3, 4: t4}
        
        # Create Relationships (FS)
        # A -> B
        r1 = TaskRelationship(predecessor_id=1, successor_id=2, type='FS', lag=0)
        # A -> C
        r2 = TaskRelationship(predecessor_id=1, successor_id=3, type='FS', lag=0)
        # B -> D
        r3 = TaskRelationship(predecessor_id=2, successor_id=4, type='FS', lag=0)
        # C -> D
        r4 = TaskRelationship(predecessor_id=3, successor_id=4, type='FS', lag=0)
        
        engine.relationships = [r1, r2, r3, r4]
        
        # Build Graph manually or call load_data logic?
        # Creating manual helper to build graph structures
        engine.preds = {
            2: [r1],
            3: [r2],
            4: [r3, r4]
        }
        engine.succs = {
            1: [r1, r2],
            2: [r3],
            3: [r4]
        }
        
        # Run Schedule
        start = datetime(2024, 1, 1, 8, 0)
        engine.calculate_dates(start)
        
        # Expected Results:
        # A: ES=Jan1 8am, EF=Jan1 1pm ?? 
        # Duration is hours in model?
        # logic: start + duration (hours)
        
        # A (5h): 8:00 -> 13:00
        self.assertEqual(t1.early_start, start)
        self.assertEqual(t1.early_finish, start + timedelta(hours=5))
        
        # B (3h): starts after A (13:00) -> 16:00
        self.assertEqual(t2.early_start, t1.early_finish)
        
        # C (4h): starts after A (13:00) -> 17:00
        self.assertEqual(t3.early_start, t1.early_finish)
        
        # D (2h): starts after max(B.EF, C.EF) = max(16:00, 17:00) = 17:00
        # EF = 19:00
        self.assertEqual(t4.early_start, t3.early_finish)
        
        # Project Finish = 19:00
        
        # Backward Pass
        # D: LF = 19:00. LS = 17:00. Float = 0.
        self.assertEqual(t4.late_finish, t4.early_finish)
        self.assertEqual(t4.total_float, 0.0)
        
        # C: LF = D.LS = 17:00. LS = 13:00. Float = 0 (Critical)
        self.assertEqual(t3.late_finish, t4.late_start)
        self.assertEqual(t3.total_float, 0.0)
        
        # B: LF = D.LS = 17:00. LS = 14:00. Float = 1.0 (Non-Critical)
        self.assertEqual(t2.late_finish, t4.late_start)
        self.assertEqual(t2.total_float, 1.0)
        
        print("CPM Logic Verified Successfully")

if __name__ == '__main__':
    unittest.main()
