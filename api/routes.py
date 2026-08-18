import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import FileResponse

from api.schemas import UploadResponse, StatusResponse
from src.pipeline.orchestrator import run_pipeline
from config.settings import RAW_DIR, OUTPUT_DIR

router = APIRouter()
jobs: dict[str, dict] = {}


@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile):
    job_id = str(uuid.uuid4())
    video_path = RAW_DIR / f"{job_id}_{file.filename}"
    with open(video_path, "wb") as f:
        f.write(await file.read())

    jobs[job_id] = {"status": "processing", "stage": "queued"}

    import asyncio
    asyncio.create_task(_run_job(job_id, video_path))

    return UploadResponse(job_id=job_id)


async def _run_job(job_id: str, video_path: Path):
    try:
        await run_pipeline(video_path, job_id, jobs)
        jobs[job_id]["status"] = "complete"
    except Exception as exc:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(exc)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return StatusResponse(job_id=job_id, **job)


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    if job_id not in jobs or jobs[job_id].get("status") != "complete":
        raise HTTPException(status_code=404, detail="Result not ready")
    output_path = OUTPUT_DIR / f"{job_id}.mp4"
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Output file missing")
    return FileResponse(output_path, filename=f"accessible_{job_id}.mp4")
