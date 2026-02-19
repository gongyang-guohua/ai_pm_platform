
import unittest
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.baseline_service import BaselineService
from app.models.project import Project, Task
from app.models.baseline import ProjectBaseline, TaskBaseline

class MockSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = None

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        # Assign IDs to mock objects
        for i, obj in enumerate(self.added):
            if not getattr(obj, 'id', None):
                obj.id = i + 1

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed = obj

    async def execute(self, statement):
        # Very limited mock for execute
        class MockResult:
            def __init__(self, items):
                self.items = items
            def scalars(self):
                return self
            def first(self):
                return self.items[0] if self.items else None
            def all(self):
                return self.items

        # Deduce what's being asked
        stmt_str = str(statement)
        if "FROM projects" in stmt_str:
            # Return a project with tasks
            p = Project(id=1, title="Test Project")
            p.tasks = [
                Task(id=1, title="Task 1", early_start=datetime(2024,1,1), early_finish=datetime(2024,1,5), original_duration=40.0, status="not_started"),
                Task(id=2, title="Task 2", early_start=datetime(2024,1,8), early_finish=datetime(2024,1,10), original_duration=16.0, status="in_progress")
            ]
            return MockResult([p])
        
        if "FROM tasks" in stmt_str:
             return MockResult([
                Task(id=1, title="Task 1", early_start=datetime(2024,1,2), early_finish=datetime(2024,1,6), original_duration=40.0, status="in_progress"),
                Task(id=2, title="Task 2", early_start=datetime(2024,1,8), early_finish=datetime(2024,1,10), original_duration=16.0, status="completed")
             ])

        if "FROM task_baselines" in stmt_str:
             return MockResult([
                 TaskBaseline(task_id=1, early_start=datetime(2024,1,1), early_finish=datetime(2024,1,5), duration=40.0, status="not_started"),
                 TaskBaseline(task_id=2, early_start=datetime(2024,1,8), early_finish=datetime(2024,1,10), duration=16.0, status="in_progress")
             ])

        return MockResult([])

class TestBaselineLogic(unittest.IsolatedAsyncioTestCase):
    async def test_create_baseline(self):
        session = MockSession()
        service = BaselineService(session)
        
        baseline = await service.create_baseline(1, "Initial Baseline", "Test Desc")
        
        self.assertEqual(baseline.name, "Initial Baseline")
        self.assertTrue(session.committed)
        # Check if TaskBaselines were added
        task_baselines = [obj for obj in session.added if isinstance(obj, TaskBaseline)]
        self.assertEqual(len(task_baselines), 2)
        self.assertEqual(task_baselines[0].early_start, datetime(2024,1,1))

    async def test_compare_baseline(self):
        session = MockSession()
        service = BaselineService(session)
        
        variances = await service.compare_baseline(1, 1)
        
        self.assertEqual(len(variances), 2)
        
        # Task 1: Start was Jan 1, now Jan 2. Variance = 24h.
        v1 = next(v for v in variances if v["task_id"] == 1)
        self.assertEqual(v1["variance_start_hours"], 24.0)
        self.assertEqual(v1["variance_finish_hours"], 24.0)
        self.assertTrue(v1["status_changed"])

        # Task 2: No date change.
        v2 = next(v for v in variances if v["task_id"] == 2)
        self.assertEqual(v2["variance_start_hours"], 0.0)
        self.assertTrue(v2["status_changed"])

if __name__ == '__main__':
    unittest.main()
