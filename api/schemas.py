from pydantic import BaseModel


class UploadResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    job_id: str
    status: str
    stage: str | None = None
    segments_generated: int | None = None
    audio_added_seconds: float | None = None
    error: str | None = None
