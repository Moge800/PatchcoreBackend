"""
画像キャッシュルーター

モデルスコープでの推論結果画像のキャッシュ一覧・取得・クリアを提供します。
"""

from typing import Optional

import cv2
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, Response

from src.api.services.model_registry import ModelRegistry

router = APIRouter(prefix="/models", tags=["images"])


def _get_registry(request: Request) -> ModelRegistry:
    return request.app.state.registry  # type: ignore[no-any-return]


def _get_loaded_engine(registry: ModelRegistry, model_name: str):
    """ロード済みエンジンを取得。未ロードなら適切なエラーを raise する"""
    try:
        return registry.get_engine(model_name)
    except KeyError:
        return None
    except RuntimeError:
        return None


@router.get("/{model_name}/images")
async def list_images(
    model_name: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    prefix: Optional[str] = Query(None, pattern="^(org|ovr)$"),
    label: Optional[str] = Query(None, pattern="^(OK|NG)$"),
    reverse_list: bool = Query(False),
) -> JSONResponse:
    """モデルのキャッシュ画像 ID 一覧を返す"""
    registry = _get_registry(request)
    engine = _get_loaded_engine(registry, model_name)

    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": f"Model '{model_name}' is not loaded"},
        )

    image_list = engine.get_store_image_list()

    if prefix:
        image_list = [i for i in image_list if i.startswith(prefix)]
    if label:
        image_list = [i for i in image_list if label in i]
    if reverse_list:
        image_list.reverse()

    return JSONResponse(content={"image_list": image_list[:limit]})


@router.get("/{model_name}/images/{image_id}")
async def get_image(model_name: str, image_id: str, request: Request) -> Response:
    """キャッシュされた画像を PNG で返す"""
    registry = _get_registry(request)
    engine = _get_loaded_engine(registry, model_name)

    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": f"Model '{model_name}' is not loaded"},
        )

    image = engine.get_image_by_id(image_id)
    if image is None:
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    _, buffer = cv2.imencode(".png", image)
    return Response(content=buffer.tobytes(), media_type="image/png")


@router.post("/{model_name}/images/clear")
async def clear_images(
    model_name: str,
    request: Request,
    execute: bool = Query(False),
) -> JSONResponse:
    """モデルの画像キャッシュをクリアする（execute=true 必須）"""
    registry = _get_registry(request)
    engine = _get_loaded_engine(registry, model_name)

    if engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": f"Model '{model_name}' is not loaded"},
        )

    if execute:
        engine.clear_store_image()
        return JSONResponse(content={"status": "cleared"})
    return JSONResponse(content={"status": "skipped"})
