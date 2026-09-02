from fastapi import APIRouter

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    return {"detail": "Not implemented yet"}
