# AI Project Management Platform / AI项目管理平台

## Getting Started / 快速开始

### Backend / 后端 (Python/FastAPI)

1. Navigate to `backend` directory / 进入 backend 目录:
   ```bash
   cd backend
   ```
2. Create virtual environment and install dependencies using uv / 创建虚拟环境并使用 uv 安装依赖:
   ```bash
   # Create virtual environment / 创建虚拟环境
   uv venv

   # Activate virtual environment (Windows) / 激活虚拟环境 (Windows)
   .venv\Scripts\activate

   # Install dependencies / 安装依赖
   uv pip install -e .
   ```
3. Initialize Database / 初始化数据库:
   ```bash
   # Make sure you are in the backend directory / 确保在 backend 目录下
   alembic upgrade head
   ```

4. Run the server / 启动服务器:
   ```bash
   run.bat
   # OR / 或者
   uvicorn app.main:app --reload
   ```
   API Docs / API 文档: http://localhost:8000/docs

### Frontend / 前端 (TypeScript/Next.js)

1. Navigate to `frontend` directory / 进入 frontend 目录:
   ```bash
   cd frontend
   ```
2. Install dependencies / 安装依赖:
   ```bash
   npm install
   ```
3. Run the development server / 启动开发服务器:
   ```bash
   npm run dev
   ```
   App / 应用地址: http://localhost:3000
