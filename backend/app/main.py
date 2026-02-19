import sys
import asyncio

# Windows 兼容性补丁 / Windows Compatibility Patch
# 必须在任何数据库驱动初始化之前执行 / Must run before any DB driver initialization
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api import api_router
from fastapi.responses import JSONResponse
from fastapi import Request


print(f"DEBUG: Loaded DATABASE_URL scheme: {settings.DATABASE_URL.split('://')[0]}")
print(f"DEBUG: Google API Key Present: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")

# 初始化 FastAPI 应用
# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=True # Enable debug mode for more verbose errors
)

# Global Exception Handler for debugging
@app.middleware("http")
async def log_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        import traceback
        error_msg = "".join(traceback.format_exception(None, exc, exc.__traceback__))
        print(f"CRITICAL UNHANDLED ERROR: {error_msg}")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "trace": str(exc)})

# 配置 CORS (跨域资源共享)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"Global exception caught: {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )

# 注册 API 路由
# Register API router
app.include_router(api_router, prefix=settings.API_V1_STR)

from app.core.templates import ENGINEERING_TEMPLATES

@app.get(f"{settings.API_V1_STR}/templates")
async def get_templates():
    """
    Get all engineering templates / 获取所有工程模板
    """
    return ENGINEERING_TEMPLATES

@app.get("/")
async def root():
    """
    Root endpoint / 根端点
    """
    return {"message": "Welcome to AI Project Management Platform API / 欢迎使用AI项目管理平台API"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint / 健康检查端点
    """
    return {"status": "healthy"}
