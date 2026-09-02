from datetime import UTC

from sqids import Sqids
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.sqids = Sqids()

    def generate_id(self) -> str:
        import time

        return self.sqids.encode([int(time.time() * 1000)])

    async def get_by_id(self, job_id: str) -> Job | None:
        return await self.session.get(Job, job_id)

    async def create(self, job_type: str) -> Job:
        job = Job(id=self.generate_id(), job_type=job_type)
        self.session.add(job)
        await self.session.flush()
        return job

    async def update_status(
        self,
        job: Job,
        status: JobStatus,
        progress: int | None = None,
        error_info: dict | None = None,
    ) -> Job:
        from datetime import datetime

        job.status = status
        if progress is not None:
            job.progress = progress
        if error_info is not None:
            job.error_info = error_info

        now = datetime.now(UTC)
        if status == JobStatus.processing and job.started_at is None:
            job.started_at = now
        elif status in (JobStatus.completed, JobStatus.failed):
            job.completed_at = now

        await self.session.flush()
        return job
