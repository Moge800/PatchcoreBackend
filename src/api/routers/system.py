"""
システム情報ルーター

OS、CPU、メモリ、GPU などのシステム情報を返します。
"""

import platform

import psutil
import torch
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.ml_engines.PatchCore.utils.device_utils import (
    check_gpu_environment,
    get_gpu_memory_info,
)

router = APIRouter(tags=["system"])


@router.get("/system_info")
async def system_info() -> JSONResponse:
    """OS、CPU、メモリ、PyTorch バージョンなどのシステム情報を返す"""
    try:
        info = {
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": f"{psutil.virtual_memory().total / 1e9:.1f}GB",
            "memory_available": f"{psutil.virtual_memory().available / 1e9:.1f}GB",
            "pytorch_version": torch.__version__,
            "cuda_support": torch.cuda.is_available(),
        }
        return JSONResponse(content=info)
    except Exception as e:
        return JSONResponse(
            content={"error": f"システム情報の取得に失敗: {str(e)}"}, status_code=500
        )


@router.get("/gpu_info")
async def gpu_info() -> JSONResponse:
    """GPU / CUDA 情報を返す"""
    info = check_gpu_environment()
    info["memory"] = get_gpu_memory_info()

    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            info[f"gpu_{i}_properties"] = {
                "name": props.name,
                "total_memory": f"{props.total_memory / 1e9:.1f}GB",
                "multi_processor_count": props.multi_processor_count,
                "major": props.major,
                "minor": props.minor,
            }

    return JSONResponse(content=info)
