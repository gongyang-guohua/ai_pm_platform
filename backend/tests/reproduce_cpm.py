
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime, timedelta
from app.services.scheduling_engine import SchedulingEngine
from app.models.project import Task, TaskRelationship

# Mock Session not needed if we populate engine manually as in test_cpm_logic.py
class MockSession:
    pass

async def text_cpm_scenarios():
    engine = SchedulingEngine(MockSession(), 1)
    
    # helper
    def create_task(tid, duration):
        return Task(id=tid, original_duration=duration, constraint_type=None)

    # Scenario 1: SS Relationship with Lag
    # A (5d) -> B (3d). SS + 2d Lag.
    # A Starts T. B Starts T + 2d.
    print("--- Scenario 1: SS + Lag ---")
    t1 = create_task(1, 40) # 5 days
    t2 = create_task(2, 24) # 3 days
    
    tasks = {1: t1, 2: t2}
    engine.tasks = tasks
    
    # A -> B (SS, lag=16h (2 days))
    r1 = TaskRelationship(predecessor_id=1, successor_id=2, type='SS', lag=16)
    
    engine.relationships = [r1]
    engine.preds = {2: [r1]}
    engine.succs = {1: [r1]}
    
    start = datetime(2024, 1, 1, 8, 0)
    engine.calculate_dates(start)
    
    print(f"Task A Start: {t1.early_start} (Exp: {start})")
    print(f"Task B Start: {t2.early_start} (Exp: {start + timedelta(hours=16)})")
    
    # Scenario 2: FF Relationship with Lead (Negative Lag)
    # C (5d) -> D (3d). FF - 1d Lag.
    # C Finishes T+5d. D Finishes T+5d - 1d = T+4d.
    # D Duration 3d -> D Start = T+4d - 3d = T+1d.
    print("\n--- Scenario 2: FF + Lead (Negative Lag) ---")
    t3 = create_task(3, 40) # 5d
    t4 = create_task(4, 24) # 3d
    
    tasks = {3: t3, 4: t4}
    engine.tasks = tasks
    
    # C -> D (FF, lag=-8h)
    r2 = TaskRelationship(predecessor_id=3, successor_id=4, type='FF', lag=-8)
    
    engine.relationships = [r2]
    engine.preds = {4: [r2]}
    engine.succs = {3: [r2]}
    
    engine.calculate_dates(start)
    
    c_finish = start + timedelta(hours=40)
    d_finish_exp = c_finish + timedelta(hours=-8)
    d_start_exp = d_finish_exp - timedelta(hours=24)
    
    print(f"Task C Finish: {t3.early_finish} (Exp: {c_finish})")
    print(f"Task D Finish: {t4.early_finish} (Exp: {d_finish_exp})")
    print(f"Task D Start:  {t4.early_start}  (Exp: {d_start_exp})")

    # Scenario 3: SF Relationship
    # E (1d) -> F (1d). SF.
    # E Starts T. F Finishes when E Starts. 
    # F Finish = T. F Start = T - 1d.
    # Note: If start date is constrained, F might need to shift?
    # Usually CPM restricts tasks to Project Start.
    print("\n--- Scenario 3: SF ---")
    t5 = create_task(5, 8) # 1d
    t6 = create_task(6, 8) # 1d
    
    tasks = {5: t5, 6: t6}
    engine.tasks = tasks
    
    # E -> F (SF, lag=0)
    r3 = TaskRelationship(predecessor_id=5, successor_id=6, type='SF', lag=0)
    
    engine.relationships = [r3]
    engine.preds = {6: [r3]}
    engine.succs = {5: [r3]}
    
    # If standard logic:
    # F.EF = E.ES + Lag = T
    # F.ES = T - 8h.
    # But max_es init to project_start (T). 
    # Current logic: max_es = project_start.
    # Then considers preds. 
    # date = pred.early_start (T). - Duration (8h). -> T-8h.
    # if date > max_es? T-8h > T? No.
    # So F.ES will remain T.
    
    engine.calculate_dates(start)
    
    print(f"Task E Start: {t5.early_start}")
    print(f"Task F Start: {t6.early_start}")
    print(f"Task F Finish: {t6.early_finish}")


if __name__ == "__main__":
    asyncio.run(text_cpm_scenarios())
