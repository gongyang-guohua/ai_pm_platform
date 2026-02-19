import asyncio
from app.core.database import Base, engine
from app.models.project import Project, Task, Material, Blueprint
from app.models.report import ProjectReport

async def sync_db():
    print("Starting DB sync...")
    async with engine.begin() as conn:
        # Warning: This approach works for adding columns if using SQLite or if columns are nullable
        # For professional migrations, Alembic is preferred.
        # Here we just ensure all tables exist. 
        # Note: SQLAlchemy's create_all does NOT add columns to existing tables.
        # If we need to add columns, we might need a direct SQL command.
        await conn.run_sync(Base.metadata.create_all)
    print("DB sync complete.")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(sync_db())
