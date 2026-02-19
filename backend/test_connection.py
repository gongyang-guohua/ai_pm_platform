import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys
import selectors

async def test_conn(url):
    print(f"Testing URL: {url}")
    try:
        engine = create_async_engine(url)
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("Success!")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

async def main():
    # Try literal with new password @
    print("--- Test 1: Literal @ ---")
    await test_conn("postgresql+psycopg://postgres:20080217@localhost:5432/project_management")
    
    # Try encoded @ -> %40
    print("\n--- Test 2: Encoded %40 ---")
    await test_conn("postgresql+psycopg://postgres:20080217%40@localhost:5432/project_management")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
