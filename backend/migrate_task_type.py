import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate_task_type():
    print("Adding task_type to 'tasks' table...")
    async with engine.begin() as conn:
        try:
            check_query = text("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name='tasks' AND column_name='task_type';
            """)
            result = await conn.execute(check_query)
            count = result.scalar()
            
            if count == 0:
                print("Adding column task_type...")
                await conn.execute(text("ALTER TABLE tasks ADD COLUMN task_type VARCHAR DEFAULT 'task';"))
            else:
                print("Column task_type already exists.")
        except Exception as e:
            print(f"Error adding task_type: {e}")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_task_type())
