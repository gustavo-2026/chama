from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Chama API"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./chama.db"
    
    # Auth - CRITICAL: Change in production!
    SECRET_KEY: str = "change-me-in-production-min-32-characters"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # M-Pesa
    MPESA_ENV: str = "sandbox"
    MPESA_CONSUMER_KEY: Optional[str] = None
    MPESA_CONSUMER_SECRET: Optional[str] = None
    MPESA_SHORTCODE: Optional[str] = None
    MPESA_PASSKEY: Optional[str] = None
    MPESA_CALLBACK_URL: Optional[str] = None
    
    # Africa's Talking (SMS)
    AT_API_KEY: Optional[str] = None
    AT_USERNAME: Optional[str] = None
    
    # Redis
    REDIS_URL: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
