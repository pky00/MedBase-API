from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str = ""
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Application
    DEBUG: bool = False
    CORS_ORIGINS: str = "*"
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MedBase API"

    # Lightsail Object Storage
    LIGHTSAIL_BUCKET_NAME: str = ""
    LIGHTSAIL_ACCESS_KEY: str = ""
    LIGHTSAIL_SECRET_KEY: str = ""
    LIGHTSAIL_ENDPOINT: str = ""
    LIGHTSAIL_REGION: str = "us-east-1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
