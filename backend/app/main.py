from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.clients.tmdb_client import TMDBClient
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    tmdb_client = TMDBClient(api_key=settings.TMDB_API_KEY)
    app.state.tmdb_client = tmdb_client
    yield
    await tmdb_client.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Movie Explorer",
        description="Movie discovery, search, import, and watchlist management",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.jobs import router as jobs_router
    from app.api.movies import router as movies_router
    from app.api.search import router as search_router
    from app.api.watchlist import router as watchlist_router

    app.include_router(movies_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(watchlist_router, prefix="/api/v1")
    app.include_router(jobs_router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
