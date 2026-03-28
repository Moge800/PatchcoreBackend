"""
モデル管理ルーター

モデルのロード・アンロード・削除・一覧・ステータス確認を提供します。
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.api.services.model_registry import ModelRegistry

router = APIRouter(prefix="/models", tags=["models"])


def _get_registry(request: Request) -> ModelRegistry:
    return request.app.state.registry  # type: ignore[no-any-return]


@router.get("")
async def list_models(request: Request) -> JSONResponse:
    """利用可能な全モデルをロード状態込みで返す"""
    registry = _get_registry(request)
    entries = registry.list_models()
    return JSONResponse(
        content={
            "models": [
                {
                    "name": e.name,
                    "status": e.status,
                    "loaded_at": e.loaded_at.isoformat() if e.loaded_at else None,
                    "error": e.error,
                }
                for e in entries
            ]
        }
    )


@router.get("/{model_name}/status")
async def model_status(model_name: str, request: Request) -> JSONResponse:
    """指定モデルのステータス・デバイス・キャッシュ数を返す"""
    registry = _get_registry(request)
    entries = {e.name: e for e in registry.list_models()}

    if model_name not in entries:
        return JSONResponse(
            status_code=404, content={"error": f"Model '{model_name}' not found"}
        )

    entry = entries[model_name]
    info: dict = {"name": entry.name, "status": entry.status}

    if entry.engine is not None and entry.status == "loaded":
        engine = entry.engine
        info["device"] = str(engine.device)
        info["image_cache"] = len(engine.get_store_image_list())

    return JSONResponse(content=info)


@router.post("/{model_name}/load")
async def load_model(model_name: str, request: Request) -> JSONResponse:
    """モデルをメモリにロードする"""
    registry = _get_registry(request)
    try:
        entry = await registry.load(model_name)
        return JSONResponse(
            content={
                "status": "loaded",
                "name": entry.name,
                "loaded_at": entry.loaded_at.isoformat() if entry.loaded_at else None,
            }
        )
    except ValueError as e:
        return JSONResponse(status_code=409, content={"error": str(e)})
    except FileNotFoundError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/{model_name}/unload")
async def unload_model(model_name: str, request: Request) -> JSONResponse:
    """モデルをメモリからアンロードする（ファイルは残す）"""
    registry = _get_registry(request)
    try:
        await registry.unload(model_name)
        return JSONResponse(content={"status": "unloaded", "name": model_name})
    except KeyError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except ValueError as e:
        return JSONResponse(status_code=409, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.delete("/{model_name}")
async def delete_model(model_name: str, request: Request) -> JSONResponse:
    """モデルをアンロードし、ディスク上のファイルも削除する"""
    registry = _get_registry(request)
    try:
        await registry.delete(model_name)
        return JSONResponse(content={"status": "deleted", "name": model_name})
    except KeyError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
