from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = 'sqlite+aiosqlite:///./uamd.db'
    DATABASE_URL_SYNC: str = 'sqlite:///./uamd.db'
    
    LLM_PROVIDER: str = 'openai'
    LLM_API_KEY: str = ''
    LLM_MODEL: str = 'gpt-4o-mini'
    
    ALLOWED_ORIGINS: str = 'http://localhost:3000'
    SECRET_KEY: str = 'super-secret-key'
    
    MAX_FILE_SIZE_IMAGE: int = 10485760
    MAX_FILE_SIZE_VIDEO: int = 104857600
    MAX_FILE_SIZE_PDF: int = 26214400
    MAX_FILE_SIZE_AUDIO: int = 52428800
    MAX_FILE_SIZE_DOCUMENT: int = 26214400
    
    MODEL_PATH: str = './models'
    
    ENABLE_AUDIO_PROCESSING: bool = False
    ENABLE_VIDEO_PROCESSING: bool = True
    ENABLE_LLM: bool = True
    
    RATE_LIMIT_PER_MINUTE: int = 30
    LOG_LEVEL: str = 'INFO'
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    
    @property
    def allowed_origins_list(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',') if origin.strip()]

    @property
    def async_database_url(self) -> str:
        """Returns an asyncpg-compatible PostgreSQL or aiosqlite SQLite URL."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Returns a psycopg2-compatible synchronous URL for Alembic migrations."""
        url = self.DATABASE_URL_SYNC or self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        elif url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url


settings = Settings()
