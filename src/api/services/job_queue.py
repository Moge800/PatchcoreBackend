"""
非同期ジョブキューサービス

推論リクエストをキューに積み、シングルワーカーで順番に処理します。
GPU 推論はスレッドプールで実行し、イベントループをブロックしません。
"""

import asyncio
import io
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image

from src.config import env_loader
from src.utils.logger import setup_logger
from src.api.services.model_registry import ModelRegistry

logger = setup_logger("job_queue", log_dir=env_loader.LOG_DIR + "/api")


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PredictJob:
    job_id: str
    model_name: str
    image_bytes: Optional[bytes]  # 完了後に None にしてメモリ解放
    detail_level: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = field(default=None)
    completed_at: Optional[datetime] = field(default=None)
    result: Optional[Dict[str, Any]] = field(default=None)
    error: Optional[str] = field(default=None)


def _bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    """アップロードされたバイト列を BGR numpy 配列に変換"""
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb = np.array(pil_img)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


class JobQueue:
    """
    推論ジョブを管理する非同期キュー。

    - enqueue() でジョブを登録し job_id を即返却
    - バックグラウンドワーカーが順次処理
    - get_job() でステータス・結果をポーリング
    - TTL 超過ジョブは定期的にクリーンアップ
    """

    def __init__(self, registry: ModelRegistry, ttl_seconds: int = 3600) -> None:
        self._registry = registry
        self._ttl = ttl_seconds
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: Dict[str, PredictJob] = {}
        self._worker_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]
        self._cleanup_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

    async def start(self) -> None:
        """バックグラウンドタスクを起動する（FastAPI lifespan から呼ぶ）"""
        self._worker_task = asyncio.create_task(self._worker(), name="job_worker")
        self._cleanup_task = asyncio.create_task(self._cleanup(), name="job_cleanup")
        logger.info("JobQueue started")

    async def stop(self) -> None:
        """バックグラウンドタスクを停止する（FastAPI lifespan から呼ぶ）"""
        for task in (self._worker_task, self._cleanup_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("JobQueue stopped")

    async def enqueue(
        self, model_name: str, image_bytes: bytes, detail_level: str = "basic"
    ) -> PredictJob:
        """
        推論ジョブをキューに登録する。

        Returns:
            作成された PredictJob（status="pending"）
        """
        job = PredictJob(
            job_id=uuid.uuid4().hex,
            model_name=model_name,
            image_bytes=image_bytes,
            detail_level=detail_level,
            status=JobStatus.PENDING,
            created_at=datetime.now(),
        )
        self._jobs[job.job_id] = job
        await self._queue.put(job.job_id)
        logger.info(f"Job enqueued: {job.job_id} model={model_name}")
        return job

    def get_job(self, job_id: str) -> Optional[PredictJob]:
        """ジョブを取得する（存在しない場合は None）"""
        return self._jobs.get(job_id)

    def list_jobs(
        self,
        model_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[PredictJob]:
        """
        ジョブ一覧を返す（新しい順、フィルタ可能）。
        """
        jobs = list(self._jobs.values())
        if model_name:
            jobs = [j for j in jobs if j.model_name == model_name]
        if status:
            jobs = [j for j in jobs if j.status == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    async def _worker(self) -> None:
        """シングルワーカー：キューからジョブを取り出して順番に処理"""
        loop = asyncio.get_event_loop()
        while True:
            job_id = await self._queue.get()
            job = self._jobs.get(job_id)
            if job is None:
                self._queue.task_done()
                continue

            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            logger.info(f"Job started: {job_id}")

            try:
                engine = self._registry.get_engine(job.model_name)
                image_bytes = job.image_bytes
                assert image_bytes is not None

                # ブロッキング処理をスレッドプールで実行
                bgr_img = await loop.run_in_executor(None, _bytes_to_bgr, image_bytes)
                raw_result = await loop.run_in_executor(None, engine.predict, bgr_img)

                # detail_level に応じてフィールドを絞る
                result: Dict[str, Any] = {
                    "label": raw_result["label"],
                    "image_id": raw_result["image_id"],
                }
                if job.detail_level == "full":
                    result["thresholds"] = raw_result["thresholds"]
                    result["z_stats"] = raw_result["z_stats"]
                else:
                    # basic: z_stats は最小限（area, maxval のみ）
                    z = raw_result["z_stats"]
                    result["z_stats"] = {"area": z["area"], "maxval": z["maxval"]}

                job.result = result
                job.status = JobStatus.COMPLETED
                logger.info(f"Job completed: {job_id} label={result['label']}")

            except KeyError as e:
                job.error = f"Model not found: {e}"
                job.status = JobStatus.FAILED
                logger.error(f"Job failed (model not found): {job_id} - {e}")
            except RuntimeError as e:
                job.error = f"Model not loaded: {e}"
                job.status = JobStatus.FAILED
                logger.error(f"Job failed (model not loaded): {job_id} - {e}")
            except Exception as e:
                job.error = str(e)
                job.status = JobStatus.FAILED
                logger.error(f"Job failed: {job_id} - {e}", exc_info=True)
            finally:
                job.completed_at = datetime.now()
                job.image_bytes = None  # メモリ解放
                self._queue.task_done()

    async def _cleanup(self) -> None:
        """TTL 超過ジョブを 60 秒ごとに削除"""
        while True:
            await asyncio.sleep(60)
            now = datetime.now()
            to_delete = [
                job_id
                for job_id, job in self._jobs.items()
                if job.completed_at is not None
                and (now - job.completed_at).total_seconds() > self._ttl
            ]
            for job_id in to_delete:
                del self._jobs[job_id]
            if to_delete:
                logger.info(f"Cleaned up {len(to_delete)} expired jobs")
