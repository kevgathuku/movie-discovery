from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8"}

    TMDB_API_KEY: str
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/moviediscovery"
    REDIS_URL: str = "redis://localhost:6379/0"

    # 002-user-auth: no default — app fails fast at startup when unset (FR-014)
    JWT_SECRET_KEY: str = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    # Comma-separated browser origins; empty = same-origin only
    CORS_ORIGINS: str = ""


settings = Settings()
