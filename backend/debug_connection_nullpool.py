import asyncio
import sys
import os
from sqlalchemy.pool import NullPool

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from sqlalchemy import text

async def main():
    print("Testing DB connection with NullPool...")
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=NullPool,
        echo=True
    )
    
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with SessionLocal() as session:
            print("Session created.")
            result = await session.execute(text("SELECT 1"))
            print(f"Result: {result.scalar()}")
            print("Connection OK.")
    except Exception as e:
        print("CONNECTION FAILED:")
        print(e)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
