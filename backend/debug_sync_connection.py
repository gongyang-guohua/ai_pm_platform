import sys
import os
from sqlalchemy import create_engine, text

# Use the same URL but with psycopg2 (default for postgresql://)
DATABASE_URL = "postgresql://postgres:20080217%40@127.0.0.1:5432/project_management"

def main():
    print("Testing SYNC DB connection...")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("Connection established.")
            result = connection.execute(text("SELECT 1"))
            print(f"Result: {result.scalar()}")
            print("Sync Connection OK.")
    except Exception as e:
        print("SYNC CONNECTION FAILED:")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
