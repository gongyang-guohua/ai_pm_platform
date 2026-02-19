import asyncio
import sys
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal, Base, engine
from app.models.project import Project, Task, TaskRelationship
from app.services.scheduling_engine import SchedulingEngine
from app.services.baseline_service import BaselineService
from app.services.evm_service import EVMService
from sqlalchemy import delete

from datetime import datetime, timedelta, timezone

async def verify_p6_features():
    print("\n--- P6 Feature Verification Test ---")
    async with AsyncSessionLocal() as db:
        # 1. Setup Test Project
        project = Project(title="P6 Verification Site", industry="Construction")
        db.add(project)
        await db.flush()
        pid = project.id

        # 2. Setup Tasks with SS/FF/FS and Lags
        # T1: Start Site (Milestone)
        # T2: Foundation (Start Site SS + 2 days LAG)
        # T3: Structure (Foundation FS + 5 days LAG)
        # T4: MEP (Structure SS + 3 days LAG, Structure FF + 2 days LAG) - Multiple complex float!
        
        t1 = Task(project_id=pid, title="Start", original_duration=0, task_type="milestone", planned_value=1000)
        t2 = Task(project_id=pid, title="Foundation", original_duration=80, planned_value=5000) # 10 days (8h/d)
        t3 = Task(project_id=pid, title="Structure", original_duration=160, planned_value=20000) # 20 days
        t4 = Task(project_id=pid, title="MEP", original_duration=120, planned_value=15000) # 15 days
        
        db.add_all([t1, t2, t3, t4])
        await db.flush()

        # Relationships
        rels = [
            TaskRelationship(project_id=pid, predecessor_id=t1.id, successor_id=t2.id, type="SS", lag=16), # 2 days lag
            TaskRelationship(project_id=pid, predecessor_id=t2.id, successor_id=t3.id, type="FS", lag=40), # 5 days lag
            TaskRelationship(project_id=pid, predecessor_id=t3.id, successor_id=t4.id, type="SS", lag=24), # 3 days after start
            TaskRelationship(project_id=pid, predecessor_id=t3.id, successor_id=t4.id, type="FF", lag=16), # 2 days after finish
        ]
        db.add_all(rels)
        await db.commit()

        # 3. Running Scheduling Engine
        print("\n[Step 1] Running Scheduling Engine...")
        engine_svc = SchedulingEngine(db, pid)
        await engine_svc.load_data()
        # Use timezone-aware datetime
        engine_svc.calculate_dates(datetime(2025, 1, 1, 8, 0, tzinfo=timezone.utc)) # Start Jan 1st
        await engine_svc.save_dates()
        await db.commit()
        
        # Verify T2 Dates
        await db.refresh(t2)
        print(f"T2 (Foundation) ES: {t2.early_start}, EF: {t2.early_finish}")
        # Expected: ES=Jan 1 + 2 days = Jan 3. EF=Jan 3 + 10 days = Jan 13.
        
        # 4. Creating Baseline
        print("\n[Step 2] Creating Initial Baseline...")
        base_svc = BaselineService(db)
        baseline = await base_svc.create_baseline(pid, "Contract Baseline")
        print(f"Baseline '{baseline.name}' created with ID {baseline.id}")

        # 5. Simulate Delay & Calculate Variance
        print("\n[Step 3] Simulating Delay...")
        t2.early_start += timedelta(days=5) # Site delayed
        t2.early_finish += timedelta(days=5)
        await db.commit()
        
        variances = await base_svc.calculate_variance(pid, baseline.id)
        for v in variances:
            if v['task_id'] == t2.id:
                print(f"Variance detected for T2: {v['finish_variance_hours']} hours delay")

        # 6. EVM Check
        print("\n[Step 4] Checking EVM Metrics...")
        # Mark T1 as completed
        t1.status = "completed"
        t1.earned_value = 1000
        t1.actual_cost = 1100
        await db.commit()
        
        evm_svc = EVMService(db)
        metrics = await evm_svc.calculate_project_metrics(pid)
        print(f"Project SPI: {metrics['SPI']}, CPI: {metrics['CPI']}, Status: {metrics['status']}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_p6_features())
