import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.tasks.sync_popular_movies")
def sync_popular_movies() -> str:
    import asyncio

    from app.clients.tmdb_client import TMDBClient
    from app.config import settings
    from app.dependencies import async_session
    from app.models.job import JobStatus
    from app.repositories.job_repo import JobRepository
    from app.services.intake import IntakeService

    async def _sync():
        tmdb_client = TMDBClient(api_key=settings.TMDB_API_KEY)
        try:
            async with async_session() as session:
                job_repo = JobRepository(session)
                job = await job_repo.create("sync_popular")
                await session.commit()

                try:
                    await job_repo.update_status(job, JobStatus.processing)
                    await session.commit()

                    service = IntakeService(session, tmdb_client)
                    filled = await service.sync_genres()
                    movies = await service.sync_popular()

                    await job_repo.update_status(
                        job, JobStatus.completed, progress=100
                    )
                    await session.commit()

                    return (
                        f"Synced {len(movies)} popular movies "
                        f"({filled} genre backfills)"
                    )
                except Exception as e:
                    await job_repo.update_status(
                        job,
                        JobStatus.failed,
                        error_info={"message": str(e)},
                    )
                    await session.commit()
                    raise
        finally:
            await tmdb_client.close()

    return asyncio.run(_sync())
