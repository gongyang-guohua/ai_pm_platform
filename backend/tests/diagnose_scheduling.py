
import asyncio
import sys
import os
import traceback
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.models.project import Project, Task, TaskRelationship
from app.services.scheduling_engine import SchedulingEngine
from sqlalchemy import select

async def diagnose():
    print("--- Starting Scheduling Diagnosis ---")
    async with AsyncSessionLocal() as session:
        # 1. Fetch all projects
        result = await session.execute(select(Project))
        projects = result.scalars().all()
        
        if not projects:
            print("No projects found in DB.")
            return

        for project in projects:
            project_id = project.id
            print(f"\n>>> Diagnosing Project ID: {project_id} ('{project.title}')")

        # 2. Load and Run Engine with detailed tracing
        try:
            engine = SchedulingEngine(session, project_id)
            print("Loading data...")
            await engine.load_data()
            print(f"Loaded {len(engine.tasks)} tasks and {len(engine.relationships)} relationships.")

            print("Starting topological sort...")
            sorted_ids = engine.topological_sort()
            print(f"Topological sort successful. {len(sorted_ids)} tasks in order.")

            print("Starting calculate_dates...")
            # Use trial of forward/backward pass with local prints if needed
            engine.calculate_dates(datetime.now())
            print("calculate_dates completed successfully.")

            print("Saving dates...")
            await engine.save_dates()
            print("save_dates completed successfully.")
            
            await session.commit()
            print("Schedule cycle completed and COMMITTED without errors.")

        except Exception as e:
            print("\n!!! ERROR DETECTED !!!")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            print("\nTraceback:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose())
