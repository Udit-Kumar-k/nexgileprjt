import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Nexgile DecarbX"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Supabase / Database Settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    DATABASE_URL: str = ""
    
    # Security
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    # Environment & CORS
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    def model_post_init(self, __context):
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "production":
                raise ValueError("CRITICAL SECURITY ERROR: SECRET_KEY environment variable must be set in production!")
            self.SECRET_KEY = "nexgile-decarbx-development-only-secret-key-do-not-use-in-production"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def effective_db_url(self) -> str:
        # If DATABASE_URL is provided (e.g. from Supabase PostgreSQL connection string), use it
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            url = self.DATABASE_URL.strip()
            # Handle postgres:// legacy prefix for SQLAlchemy
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url
        # Fallback to local SQLite for immediate standalone operation without requiring external server
        return "sqlite:///./decarbx.db"

settings = Settings()
