import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    try:
        async with engine.begin() as conn:
            print("Migrating schema...")
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS outline_level INTEGER DEFAULT 1"))
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_summary BOOLEAN DEFAULT FALSE"))
            print("Migration complete.")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
