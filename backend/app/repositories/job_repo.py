from datetime import UTC

from sqids import Sqids
from sqlalchemy import func, select
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

    async def list(
        self,
        status: JobStatus | None = None,
        job_type: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Job], int]:
        query = select(Job).order_by(Job.created_at.desc())
        if status is not None:
            query = query.where(Job.status == status)
        if job_type is not None:
            query = query.where(Job.job_type == job_type)

        total = (
            await self.session.execute(
                select(func.count()).select_from(query.subquery())
            )
        ).scalar() or 0
        jobs = list(
            (
                await self.session.execute(
                    query.offset((page - 1) * per_page).limit(per_page)
                )
            ).scalars().all()
        )
        return jobs, total

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
