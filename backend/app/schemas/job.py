from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_type: str
    status: str
    progress: int | None = None
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error_info: dict | None = None
