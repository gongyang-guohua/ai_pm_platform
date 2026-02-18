import asyncio
from sqlalchemy import inspect
from app.core.database import engine

async def check_schema():
    async with engine.connect() as conn:
        def get_columns(connection):
            inspector = inspect(connection)
            return inspector.get_columns("tasks")
            
        columns = await conn.run_sync(get_columns)
        col_names = [c["name"] for c in columns]
        print("Columns in 'tasks' table:", col_names)
        
        if "outline_level" in col_names and "is_summary" in col_names:
            print("SUCCESS: Migration applied.")
        else:
            print("FAILURE: Columns missing.")

if __name__ == "__main__":
    asyncio.run(check_schema())
