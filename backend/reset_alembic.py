import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def reset_alembic():
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM alembic_version"))
        await session.commit()
        print("Alembic version reset.")

if __name__ == "__main__":
    asyncio.run(reset_alembic())
