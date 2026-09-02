import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.clients.tmdb_client import TMDBClient
from app.config import settings
from app.exceptions import (
    ExternalAPIError,
    MovieAlreadyExistsError,
    MovieNotFoundError,
    WatchlistDuplicateError,
    WatchlistEntryNotFoundError,
    WatchlistNotFoundError,
)


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

    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(MovieNotFoundError)
    async def movie_not_found_handler(request: Request, exc: MovieNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.exception_handler(MovieAlreadyExistsError)
    async def movie_already_exists_handler(request: Request, exc: MovieAlreadyExistsError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(WatchlistNotFoundError)
    async def watchlist_not_found_handler(request: Request, exc: WatchlistNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Watchlist not found"},
        )

    @app.exception_handler(WatchlistEntryNotFoundError)
    async def watchlist_entry_not_found_handler(
        request: Request, exc: WatchlistEntryNotFoundError
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Watchlist entry not found"},
        )

    @app.exception_handler(WatchlistDuplicateError)
    async def watchlist_duplicate_handler(request: Request, exc: WatchlistDuplicateError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Movie is already in this watchlist"},
        )

    @app.exception_handler(ExternalAPIError)
    async def external_api_error_handler(request: Request, exc: ExternalAPIError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"detail": "TMDB API is currently unavailable. Please try again later."},
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
