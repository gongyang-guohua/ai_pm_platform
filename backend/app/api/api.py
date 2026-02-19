from fastapi import APIRouter
from app.api.endpoints import login, projects, tasks, tracking, blueprints, reports, risks, analytics, import_project, scheduling, baselines
# from app.api.endpoints import users # TODO: Implement users endpoint

api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(tracking.router, tags=["tracking"])
api_router.include_router(blueprints.router, prefix="/blueprints", tags=["blueprints"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(risks.router, prefix="/risks", tags=["risks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(import_project.router, prefix="/projects", tags=["import"])
api_router.include_router(scheduling.router, prefix="/projects", tags=["scheduling"])
api_router.include_router(baselines.router, prefix="/projects", tags=["baselines"])
# api_router.include_router(users.router, prefix="/users", tags=["users"])
