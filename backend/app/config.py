from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8"}

    TMDB_API_KEY: str
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/moviediscovery"
    REDIS_URL: str = "redis://localhost:6379/0"


settings = Settings()
