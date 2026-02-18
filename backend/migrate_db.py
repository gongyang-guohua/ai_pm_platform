import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate_tasks():
    print("Starting manual migration for 'tasks' table...")
    
    # List of new columns to add
    new_columns = [
        ("wbs_code", "VARCHAR"),
        ("priority", "VARCHAR DEFAULT 'Medium'"),
        ("planned_start", "TIMESTAMP WITH TIME ZONE"),
        ("planned_end", "TIMESTAMP WITH TIME ZONE"),
        ("actual_start", "TIMESTAMP WITH TIME ZONE"),
        ("actual_end", "TIMESTAMP WITH TIME ZONE"),
        ("responsible_party", "VARCHAR"),
        ("helper_party", "VARCHAR"),
        ("notes", "TEXT")
    ]
    
    async with engine.begin() as conn:
        for col_name, col_type in new_columns:
            try:
                # PostgreSQL specific: check if column exists first to avoid error
                check_query = text(f"""
                SELECT count(*) 
                FROM information_schema.columns 
                WHERE table_name='tasks' AND column_name='{col_name}';
                """)
                result = await conn.execute(check_query)
                count = result.scalar()
                
                if count == 0:
                    print(f"Adding column {col_name}...")
                    alter_query = text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type};")
                    await conn.execute(alter_query)
                else:
                    print(f"Column {col_name} already exists.")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")

        # Standardize status if needed (optional, just ensuring compatibility)
        # Update existing 'todo' to 'not_started' if we change the default
        try:
            update_status_query = text("UPDATE tasks SET status = 'not_started' WHERE status = 'todo';")
            await conn.execute(update_status_query)
            print("Standardized status from 'todo' to 'not_started'.")
        except Exception as e:
            print(f"Error standardizing status: {e}")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate_tasks())
