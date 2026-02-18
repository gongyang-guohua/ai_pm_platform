import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def check_version():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        print(f"Current Alembic Version: {version}")

if __name__ == "__main__":
    asyncio.run(check_version())
