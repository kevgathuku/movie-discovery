from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.exceptions import JobNotFoundError
from app.models.job import JobStatus
from app.repositories.job_repo import JobRepository
from app.schemas.job import JobResponse

router = APIRouter(
    prefix="/admin/jobs",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
    include_in_schema=False,
)


class AdminJobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=AdminJobListResponse)
async def list_jobs(
    status: JobStatus | None = None,
    job_type: str | None = None,
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    per_page = min(max(per_page, 1), 100)
    jobs, total = await JobRepository(db).list(
        status=status, job_type=job_type, page=page, per_page=per_page
    )
    return AdminJobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    job = await JobRepository(db).get_by_id(job_id)
    if job is None:
        raise JobNotFoundError(job_id)
    return JobResponse.model_validate(job)
