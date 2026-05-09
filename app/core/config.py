from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/market_research"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # LLM Provider Configuration
    OPENAI_API_KEY: Optional[str] = None
    
    # External APIs
    TAVILY_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
