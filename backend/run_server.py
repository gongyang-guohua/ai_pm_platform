
import uvicorn
import asyncio
import sys
import os

if __name__ == "__main__":
    # Ensure correct asyncio loop policy for Windows + asyncpg/psycopg
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Ensure app imports work by adding backend to sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
