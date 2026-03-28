"""
ジョブルーター

推論ジョブの投入・ステータス確認・一覧取得を提供します。
"""

from typing import Optional

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from src.api.services.job_queue import JobQueue, JobStatus

router = APIRouter(tags=["jobs"])


def _get_queue(request: Request) -> JobQueue:
    return request.app.state.queue  # type: ignore[no-any-return]


@router.post("/models/{model_name}/predict")
async def predict(
    model_name: str,
    request: Request,
    file: UploadFile = File(...),
    detail_level: str = Query("basic", pattern="^(basic|full)$"),
) -> JSONResponse:
    """
    推論ジョブをキューに投入する。

    job_id を即返却するので、`GET /jobs/{job_id}` でポーリングしてください。
    """
    queue = _get_queue(request)

    # モデルがロード済みか事前確認（早期エラー返却）
    try:
        request.app.state.registry.get_engine(model_name)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"error": f"Model '{model_name}' not found"}
        )
    except RuntimeError:
        return JSONResponse(
            status_code=503,
            content={"error": f"Model '{model_name}' is not loaded. POST /models/{model_name}/load first."},
        )

    image_bytes = await file.read()
    job = await queue.enqueue(model_name, image_bytes, detail_level)

    return JSONResponse(
        status_code=202,
        content={"job_id": job.job_id, "status": job.status},
    )


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request) -> JSONResponse:
    """ジョブのステータスと結果を返す"""
    queue = _get_queue(request)
    job = queue.get_job(job_id)

    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    body: dict = {
        "job_id": job.job_id,
        "model_name": job.model_name,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
    }

    if job.started_at:
        body["started_at"] = job.started_at.isoformat()
    if job.completed_at:
        body["completed_at"] = job.completed_at.isoformat()

    if job.status == JobStatus.COMPLETED:
        body["result"] = job.result
    elif job.status == JobStatus.FAILED:
        body["error"] = job.error

    return JSONResponse(content=body)


@router.get("/jobs")
async def list_jobs(
    request: Request,
    model_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> JSONResponse:
    """ジョブ一覧を返す（新しい順）"""
    queue = _get_queue(request)
    jobs = queue.list_jobs(model_name=model_name, status=status, limit=limit)

    return JSONResponse(
        content={
            "jobs": [
                {
                    "job_id": j.job_id,
                    "model_name": j.model_name,
                    "status": j.status,
                    "created_at": j.created_at.isoformat(),
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                }
                for j in jobs
            ]
        }
    )
