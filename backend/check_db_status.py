import asyncio
from app.core.database import AsyncSessionLocal
from app.models.project import Project
from sqlalchemy import select, func

async def check_db():
    async with AsyncSessionLocal() as session:
        stmt = select(func.count(Project.id))
        result = await session.execute(stmt)
        count = result.scalar()
        print(f"Total projects in database: {count}")
        
        stmt = select(Project)
        result = await session.execute(stmt)
        projects = result.scalars().all()
        for p in projects:
            print(f"Project: {p.id} - {p.title} ({p.status})")

if __name__ == "__main__":
    asyncio.run(check_db())
