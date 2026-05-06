from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str = "sqlite:///./backend/tender.db"
    
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://apie.zhisuaninfo.com/v1"
    LLM_MODEL: str = "gpt-oss-120b"
    LLM_TIMEOUT_SECONDS: int = 30
    EXTRACTION_MODE: str = "hybrid"  # rule | agent | hybrid
    
    REDIS_URL: Optional[str] = None
    
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    WEBHOOK_URL: Optional[str] = None
    

settings = Settings()
