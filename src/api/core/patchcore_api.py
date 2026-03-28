"""
PatchCore バックエンド アプリファクトリ

FastAPI アプリケーションの初期化、lifespan 管理、ルーター登録を行います。
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api.routers import images, jobs, models, system
from src.api.services.job_queue import JobQueue
from src.api.services.model_registry import ModelRegistry
from src.config import env_loader
from src.utils.logger import setup_logger

logger = setup_logger("patchcore_api", log_dir=env_loader.LOG_DIR + "/api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動
    registry = ModelRegistry()
    queue = JobQueue(registry, ttl_seconds=env_loader.JOB_QUEUE_TTL)
    await queue.start()

    startup_models = [
        m.strip() for m in env_loader.LOADED_MODELS.split(",") if m.strip()
    ]
    if startup_models:
        logger.info(f"Loading startup models: {startup_models}")
        await registry.load_startup_models(startup_models)

    app.state.registry = registry
    app.state.queue = queue

    yield

    # シャットダウン
    await queue.stop()
    logger.info("Server shutdown complete")


app = FastAPI(
    title=env_loader.APP_NAME,
    version=env_loader.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(models.router)
app.include_router(jobs.router)
app.include_router(images.router)
app.include_router(system.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.api.core.patchcore_api:app",
        host=env_loader.API_SERVER_HOST,
        port=env_loader.API_SERVER_PORT,
        use_colors=False,
        workers=1,
        reload=env_loader.API_RELOAD,
    )
