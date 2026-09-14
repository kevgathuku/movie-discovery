import logging

from celery import shared_task

logger = logging.getLogger(__name__)


async def _run_tracked_job(job_type, run):
    from app.clients.tmdb_client import TMDBClient
    from app.config import settings
    from app.dependencies import async_session
    from app.models.job import JobStatus
    from app.repositories.job_repo import JobRepository

    tmdb_client = TMDBClient(api_key=settings.TMDB_API_KEY)
    try:
        async with async_session() as session:
            job_repo = JobRepository(session)
            job = await job_repo.create(job_type)
            await session.commit()

            try:
                await job_repo.update_status(job, JobStatus.processing)
                await session.commit()

                message = await run(session, tmdb_client, job_repo, job)

                await job_repo.update_status(
                    job, JobStatus.completed, progress=100
                )
                await session.commit()

                return message
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


@shared_task(name="app.tasks.tasks.sync_popular_movies")
def sync_popular_movies() -> str:
    import asyncio

    from app.services.intake import IntakeService

    async def _sync(session, tmdb_client, job_repo, job):
        service = IntakeService(session, tmdb_client)
        filled = await service.sync_genres()
        movies = await service.sync_popular()
        return f"Synced {len(movies)} popular movies ({filled} genre backfills)"

    return asyncio.run(_run_tracked_job("sync_popular", _sync))


@shared_task(name="app.tasks.tasks.sync_imdb_ids")
def sync_imdb_ids() -> str:
    import asyncio

    from app.models.job import JobStatus
    from app.services.intake import IntakeService

    async def _sync(session, tmdb_client, job_repo, job):
        service = IntakeService(session, tmdb_client)

        async def report(attempted, total):
            if attempted % 10 == 0:
                await job_repo.update_status(
                    job,
                    JobStatus.processing,
                    progress=int(100 * attempted / max(total, 1)),
                )
                await session.commit()

        filled = await service.sync_imdb_ids(on_progress=report)
        return f"Filled {filled} IMDb IDs"

    return asyncio.run(_run_tracked_job("sync_imdb_ids", _sync))
