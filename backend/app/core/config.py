from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 项目名称 / Project Name
    PROJECT_NAME: str = "AI Project Management Platform"
    # API 前缀 / API Prefix
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置 / Database Configuration
    # 使用 PostgreSQL 并应用经过验证的编码密码 / Using PostgreSQL with verified encoded password
    DATABASE_URL: str = "postgresql+psycopg://postgres:20080217%40@localhost:5432/project_management"
    
    # 安全配置 / Security Configuration
    # 生产环境中请修改此密钥 / Change this in production
    SECRET_KEY: str = "changethis" 
    ALGORITHM: str = "HS256"
    # Token 过期时间 (分钟) / Token expiration time (minutes)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OpenAI / AI 配置
    OPENAI_API_KEY: str | None = None
    
    # Google Configuration
    GOOGLE_API_KEY: str | None = None

    # LLM Configuration
    LLM_PROVIDER: str = "local" # Options: "google", "openai", "local", "huggingface"
    MODEL_PATH: str | None = None # Path to GGUF model for local provider
    HUGGINGFACE_API_KEY: str | None = None # For remote HF Inference API

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()
