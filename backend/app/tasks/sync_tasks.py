import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.sync_tasks.sync_trending_movies")
def sync_trending_movies() -> str:
    import asyncio

    from app.clients.tmdb_client import TMDBClient
    from app.config import settings
    from app.dependencies import async_session
    from app.models.job import JobStatus
    from app.repositories.job_repo import JobRepository
    from app.services.sync_service import SyncService

    async def _sync():
        tmdb_client = TMDBClient(api_key=settings.TMDB_API_KEY)
        try:
            async with async_session() as session:
                job_repo = JobRepository(session)
                job = await job_repo.create("sync_trending")
                await session.commit()

                try:
                    await job_repo.update_status(job, JobStatus.processing)
                    await session.commit()

                    service = SyncService(session, tmdb_client)
                    movies = await service.sync_trending()

                    await job_repo.update_status(
                        job, JobStatus.completed, progress=100
                    )
                    await session.commit()

                    return f"Synced {len(movies)} trending movies"
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
