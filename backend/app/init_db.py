import asyncio
import sys
import os

# Add the current directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.database import engine, Base
from app.models.project import Project, Task, Material, Blueprint, Risk

async def init_db():
    print("Initializing database...")
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
