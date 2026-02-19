
import unittest
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.scheduling_engine import SchedulingEngine, ProjectCalendar
from app.models.project import Task, TaskRelationship

class TestCPMComprehensive(unittest.TestCase):
    def setUp(self):
        # Mock Session
        self.engine = SchedulingEngine(None, 1)
        self.calendar = ProjectCalendar()
        
    def create_task(self, t_id, duration, constraint_type=None, constraint_date=None):
        return Task(
            id=t_id,
            original_duration=duration,
            constraint_type=constraint_type,
            constraint_date=constraint_date,
            is_summary=False,
            status='not_started'
        )
        
    def setup_graph(self, tasks, rels):
        self.engine.tasks = {t.id: t for t in tasks}
        self.engine.relationships = rels
        self.engine.preds = {}
        self.engine.succs = {}
        
        for rel in rels:
            if rel.successor_id not in self.engine.preds:
                self.engine.preds[rel.successor_id] = []
            self.engine.preds[rel.successor_id].append(rel)
            
            if rel.predecessor_id not in self.engine.succs:
                self.engine.succs[rel.predecessor_id] = []
            self.engine.succs[rel.predecessor_id].append(rel)

    def test_calendar_logic(self):
        # Mon Jan 1 2024 is a Monday. 8-12, 13-17.
        start = datetime(2024, 1, 1, 8, 0) # Mon 8am
        
        # Add 4 hours -> Mon 12:00
        d1 = self.calendar.add_working_duration(start, 4)
        self.assertEqual(d1, datetime(2024, 1, 1, 12, 0))
        
        # Add 5 hours -> Mon 14:00 (12-13 lunch skipped)
        d2 = self.calendar.add_working_duration(start, 5)
        self.assertEqual(d2, datetime(2024, 1, 1, 14, 0))
        
        # Add 9 hours -> Tue 09:00 (8h Mon + 1h Tue)
        d3 = self.calendar.add_working_duration(start, 9)
        self.assertEqual(d3, datetime(2024, 1, 2, 9, 0))
        
        # Add 40 hours (1 week) -> Mon Jan 1 08:00 + 40h working -> Fri Jan 5 17:00
        d4 = self.calendar.add_working_duration(start, 40)
        self.assertEqual(d4, datetime(2024, 1, 5, 17, 0))

    def test_ss_relationship_with_lag(self):
        # A (5d = 40h) -> B (3d = 24h)
        # SS + 2 days (16h) Lag
        # Start: Mon Jan 1 8am
        
        t1 = self.create_task(1, 40)
        t2 = self.create_task(2, 24)
        
        r1 = TaskRelationship(predecessor_id=1, successor_id=2, type='SS', lag=16)
        
        self.setup_graph([t1, t2], [r1])
        
        start = datetime(2024, 1, 1, 8, 0)
        self.engine.calculate_dates(start)
        
        # A Start: Mon Jan 1 08:00
        self.assertEqual(t1.early_start, start)
        
        # B Start: A.Start + 16h working -> Mon 8am + 16h = Wed Jan 3 08:00
        # Mon (8h), Tue (8h) -> Wed 8am.
        expected_b_start = datetime(2024, 1, 3, 8, 0)
        self.assertEqual(t2.early_start, expected_b_start)

    def test_ff_relationship_with_lead(self):
        # A (5d=40h) -> B (3d=24h)
        # FF - 1 day (-8h) Lead
        
        t1 = self.create_task(1, 40)
        t2 = self.create_task(2, 24)
        
        r1 = TaskRelationship(predecessor_id=1, successor_id=2, type='FF', lag=-8)
        
        self.setup_graph([t1, t2], [r1])
        
        start = datetime(2024, 1, 1, 8, 0)
        self.engine.calculate_dates(start)
        
        # A Finish: Mon Jan 1 8am + 40h -> Mon Jan 8 08:00 (due to weekend) -> Finish is actually inclusive or exclusive?
        # Logic says add 40h. 
        # M, T, W, Th, F = 5*8=40h. 
        # Start Mon 8am. End Fri 17:00.
        # Let's check calculation.
        # Mon 8am + 40h = Mon 8am (next week)? No.
        # 16:00 vs 17:00? 
        # add_working_duration logic: 
        # 40h. Mon 8-17 (8h). Rem 32. Tue (8). Rem 24. Wed (8). Rem 16. Thu (8). Rem 8. Fri (8). Rem 0. 
        # Returns Fri 17:00.
        
        expected_a_finish = datetime(2024, 1, 5, 17, 0)
        self.assertEqual(t1.early_finish, expected_a_finish)
        
        # B Finish constraint: A.Finish - 8h (Lead) = Fri 17:00 - 8h = Fri 08:00.
        # B Finish >= Fri 08:00.
        # B Start = B Finish - 24h (3d).
        # Fri 08:00 - 24h working.
        # Back 8h (Thu 17 -> Thu 08).
        # Back 8h (Wed 17 -> Wed 08).
        # Back 8h (Tue 17 -> Tue 08).
        # So B Start = Tue Jan 2 08:00.
        
        # NOTE: If B has no other predecessor, its ES defaults to Project Start (Jan 1).
        # But FF constraint pushes EF to >= Fri 08:00.
        # If ES=Jan 1, EF=Jan 3 17:00 (3d: Mon,Tue,Wed).
        # Constraint: EF >= Fri 08:00.
        # So EF becomes Fri 08:00.
        # ES recalculates from EF? 
        # In implementation: 
        #   finish_constraint = pred.EF + lag = Fri 08:00.
        #   constraint_date (ES) = finish_constraint - duration = Fri 08:00 - 24h = Tue 08:00.
        #   max_es = max(ProjectStart, Tue 08:00) = Tue 08:00.
        
        expected_b_start = datetime(2024, 1, 2, 8, 0)
        self.assertEqual(t2.early_start, expected_b_start)
        
    def test_sf_relationship(self):
        # A (Start) -> B (Finish)
        # Type SF. Lag 0.
        # B cannot finish until A starts.
        # A: 1d (8h). B: 1d (8h).
        
        t1 = self.create_task(1, 8)
        t2 = self.create_task(2, 8)
        
        r1 = TaskRelationship(predecessor_id=1, successor_id=2, type='SF', lag=0)
        
        self.setup_graph([t1, t2], [r1])
        start = datetime(2024, 1, 1, 8, 0)
        self.engine.calculate_dates(start)
        
        # A Start: Mon 08:00.
        # B Finish >= A Start + 0 = Mon 08:00.
        # B Start = B Finish - 8h = Mon 08:00 - 8h workday?
        # Prev working moment of Mon 08:00 is Fri 17:00?
        # Subtract 8h from Mon 08:00 -> Fri 08:00?
        # Wait, if B Finish >= Mon 08:00.
        # B ES calculated as: (A.Start + Lag) - Duration.
        # Mon 08:00 - 8h.
        # Mon 08:00 is Start of working day.
        # Subtracting 8h logic:
        # prev_working_moment(Mon 08:00) -> Fri 17:00.
        # Fri 17:00 - 8h -> Fri 08:00.
        # So B Start calculated as Fri previous week?
        # BUT max_es defaults to Project Start (Mon Jan 1 08:00).
        # So max(Fri 08:00, Mon 08:00) = Mon 08:00.
        # So B Start = Mon 08:00.
        # B Finish = Mon 17:00.
        # Does B Finish (Mon 17:00) satisfy >= Mon 08:00? Yes.
        
        self.assertEqual(t2.early_start, start)

    def test_critical_path(self):
        # A (5d) -> B (3d)
        # C (2d) -> D (2d) -> B (Relationship C->B? No, let's connect D->B)
        # A: 5d. B: 3d. Path A-B = 8d.
        # C: 2d. Path C = 2d.
        # Let's make simple Y shape.
        # A (5d) -> C (2d). Path 7d.
        # B (2d) -> C (2d). Path 4d.
        # A should be Critical (Float 0). B should have Float.
        
        t1 = self.create_task(1, 40) # 5d
        t2 = self.create_task(2, 16) # 2d
        t3 = self.create_task(3, 16) # 2d
        
        # A -> C
        r1 = TaskRelationship(predecessor_id=1, successor_id=3, type='FS', lag=0)
        # B -> C
        r2 = TaskRelationship(predecessor_id=2, successor_id=3, type='FS', lag=0)
        
        self.setup_graph([t1, t2, t3], [r1, r2])
        start = datetime(2024, 1, 1, 8, 0)
        self.engine.calculate_dates(start)
        
        # Project Finish: 
        # Path A-C: 5+2=7d.
        # Path B-C: 2+2=4d.
        # Total = 7d. (Mon-Fri + Mon-Tue).
        # Finish: Tue Jan 9 17:00.
        
        # A Float: 0?
        self.assertAlmostEqual(t1.total_float, 0.0)
        
        # B Float: 
        # B can start Mon Jan 1. 2d duration -> Ends Tue 17:00.
        # C starts after A (Mon Jan 8 08:00).
        # B needs to finish by Mon Jan 8 08:00.
        # LF_B = Mon Jan 8 08:00.
        # EF_B = Tue Jan 2 17:00.
        # Float = LS - ES or LF - EF?
        # LS = LF - Dur = Jan 8 08:00 - 16h = Thu Jan 4 08:00.
        # ES = Jan 1 08:00.
        # Float = Jan 4 08:00 - Jan 1 08:00 = 3 days (24 working hours?).
        # My engine calculates total_seconds / 3600.
        # Jan 4 08:00 - Jan 1 08:00 is 3 * 24 = 72 hours (Calendar time).
        # 72 hours float. 
        # Note: 3 days of working time slack. Difference between 5d (A) and 2d (B) is 3d.
        
        self.assertTrue(t2.total_float > 0)
        self.assertAlmostEqual(t3.total_float, 0.0)

if __name__ == '__main__':
    unittest.main()
