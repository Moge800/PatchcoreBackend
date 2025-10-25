from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import JSONResponse, Response
from typing import Callable
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
from src.model.core.inference_engine import PatchCoreInferenceEngine
import time
from functools import wraps
import inspect
from src.model.utils.device_utils import get_gpu_memory_info, check_gpu_environment
import torch
from src.utils.logger import setup_logger
from src.types import DetailLevel
from src.config import env_loader

app = FastAPI(title=env_loader.APP_NAME, version=env_loader.APP_VERSION)
logger = setup_logger("patchcore_api", log_dir=env_loader.LOG_DIR + "/api")


def engine_required(func: Callable) -> Callable:
    """
    エンジンが初期化されているかチェックするデコレータ

    Args:
        func: デコレート対象の関数

    Returns:
        Callable: ラップされた関数
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs) -> JSONResponse:
        if engine is None:
            return JSONResponse(status_code=503, content={"status": "error", "message": "Engine not initialized"})
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    return async_wrapper


def reload_engine() -> None:
    """
    推論エンジンをリロードする

    環境変数からモデル名を取得し、エンジンのシングルトンインスタンスを再作成する。
    エラーが発生した場合は、エンジンをNoneに設定する。
    """
    global engine
    try:
        # .envからモデル名を取得
        model_name = env_loader.DEFAULT_MODEL_NAME
        PatchCoreInferenceEngine._instance = None
        engine = PatchCoreInferenceEngine(model_name=model_name)
        logger.info("Engine reloaded successfully")
    except Exception as e:
        logger.error(f"Failed to reload engine: {e}", exc_info=True)
        engine = None


reload_engine()


@app.post("/engine/predict")
@engine_required
async def predict(
    file: UploadFile = File(...), detail_level: DetailLevel = Query("basic", enum=["basic", "full"])
) -> JSONResponse:
    """
    画像の異常検出を実行する

    Args:
        file: アップロードされた画像ファイル（PNG, JPEG等）
        detail_level: 応答の詳細レベル
            - "basic": 基本情報のみ（label, process_time, 最小限のz_stats）
            - "full": 全情報（thresholds, 完全なz_stats含む）

    Returns:
        JSONResponse: 予測結果
            - label (str): "OK" または "NG"
            - process_time (float): 処理時間（秒）
            - image_id (str): 画像ID
            - thresholds (dict): しきい値情報
            - z_stats (dict): Z-score統計情報

    Raises:
        500: 予測処理中にエラーが発生した場合
    """
    try:
        start = time.perf_counter()

        image_bytes = await file.read()
        pil_img = Image.open(BytesIO(image_bytes)).convert("RGB")
        np_img = np.array(pil_img)
        cv_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
        result = engine.predict(cv_img)

        end = time.perf_counter()

        response_data = {
            "label": result["label"],
            "process_time": round(end - start, 2),
            "image_id": result["image_id"],
        }

        if detail_level == "full":
            response_data["thresholds"] = result["thresholds"]
            response_data["z_stats"] = result["z_stats"]
        else:
            response_data["thresholds"] = result["thresholds"]
            # basicモードでは必要最低限の統計のみ返す
            response_data["z_stats"] = {k: result["z_stats"][k] for k in ["area", "maxval"] if k in result["z_stats"]}

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/engine/restart")
async def restart_engine(execute: bool = Query(False)) -> JSONResponse:
    """
    推論エンジンを再起動する

    モデルやメモリバンクを再読み込みする。設定変更後に使用する。

    Args:
        execute: True の場合のみ実行（安全装置）

    Returns:
        JSONResponse: 実行結果
            - status (str): "reloaded" または "skipped"
            - model (str): 再読み込み後のモデル名（reloadedの場合）
    """
    if execute:
        reload_engine()
        logger.info("Engine reloaded complete")
        return JSONResponse(content={"status": "reloaded", "model": engine.get_model_name()})
    return JSONResponse(content={"status": "skipped"})


@app.get("/engine/name")
async def get_engine_name():
    return JSONResponse(content={"name": engine.get_model_name()})


@app.get("/images")
@engine_required
async def get_image_list(
    limit: int = Query(100, ge=1, le=1000),
    prefix: str = Query(None, enum=["org", "ovr"]),
    label: str = Query(None, enum=["OK", "NG"]),
    reverse_list: bool = Query(False),
) -> JSONResponse:
    """
    保存された画像のIDリストを取得する

    Args:
        limit: 取得する最大件数（1-1000、デフォルト: 100）
        prefix: フィルタするプレフィックス
            - "org": オリジナル画像のみ
            - "ovr": オーバーレイ画像のみ
            - None: すべて
        label: フィルタするラベル
            - "OK": OK画像のみ
            - "NG": NG画像のみ
            - None: すべて
        reverse_list: True の場合、リストを逆順にする

    Returns:
        JSONResponse: 画像IDのリスト
            - image_list (List[str]): 画像IDの配列
    """
    image_list = engine.get_store_image_list()
    if prefix:
        image_list = [img_id for img_id in image_list if img_id.startswith(prefix)]
    if label:
        image_list = [img_id for img_id in image_list if label in img_id]
    if reverse_list:
        image_list.reverse()
    return JSONResponse(content={"image_list": image_list[:limit]})


@app.get("/images/{image_id}")
@engine_required
async def get_image(image_id: str) -> Response:
    """
    保存された画像をIDで取得する

    Args:
        image_id: 画像ID（例: "org_20250104_120000_OK"）

    Returns:
        Response: PNG形式の画像データ

    Raises:
        404: 指定されたIDの画像が見つからない場合
    """
    image = engine.get_image_by_id(image_id)
    if image is None:
        logger.warning(f"Image not found: {image_id}")
        return JSONResponse(status_code=404, content={"error": "Image not found"})

    _, buffer = cv2.imencode(".png", image)
    return Response(content=buffer.tobytes(), media_type="image/png")


@app.post("/images/clear")
@engine_required
async def clear_image(execute: bool = Query(False)) -> JSONResponse:
    """
    画像キャッシュをクリアする

    Args:
        execute: True の場合のみ実行（安全装置）

    Returns:
        JSONResponse: 実行結果
            - status (str): "cleared" または "skipped"
    """

    if execute:
        engine.clear_store_image()
        logger.info("Image cache cleared")
        return JSONResponse(content={"status": "cleared"})
    return JSONResponse(content={"status": "skipped"})


@app.get("/status")
@engine_required
async def status() -> JSONResponse:
    """
    APIサーバーとエンジンのステータスを取得する

    Returns:
        JSONResponse: ステータス情報
            - status (str): "ok"
            - model (str): 現在のモデル名
            - image_cache (int): キャッシュされている画像の数
    """
    return JSONResponse(
        content={"status": "ok", "model": engine.get_model_name(), "image_cache": len(engine.get_store_image_list())}
    )


@app.get("/gpu_info")
@engine_required
async def gpu_info() -> JSONResponse:
    """
    GPU情報を取得する

    CUDA対応GPU、メモリ使用状況、デバイスプロパティなどの情報を返す。

    Returns:
        JSONResponse: GPU情報
            - cuda_available (bool): CUDA が利用可能か
            - cuda_version (str): CUDA バージョン
            - device_count (int): GPU デバイス数
            - current_device (str): 現在使用中のデバイス
            - mixed_precision (bool): 混合精度演算の有効/無効
            - memory (dict): メモリ使用状況
            - gpu_X_properties (dict): 各GPUのプロパティ（X=0,1,...）
    """
    # 基本情報
    info = check_gpu_environment()

    # エンジンの現在のデバイス情報
    if engine and hasattr(engine, "device"):
        info["current_device"] = str(engine.device)
        info["mixed_precision"] = getattr(engine, "use_mixed_precision", False)

    # メモリ情報
    info["memory"] = get_gpu_memory_info()

    if torch.cuda.is_available():
        # 詳細なメモリ情報
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


@app.get("/system_info")
async def system_info() -> JSONResponse:
    """
    システム情報を取得する（GPU要件なし）

    OS、CPU、メモリ、PyTorchバージョンなどのシステム情報を返す。

    Returns:
        JSONResponse: システム情報
            - platform (str): OS情報
            - cpu_count (int): CPU コア数
            - memory_total (str): 総メモリ容量
            - memory_available (str): 利用可能メモリ
            - pytorch_version (str): PyTorch バージョン
            - cuda_support (bool): CUDA サポートの有無

    Raises:
        500: システム情報の取得に失敗した場合
    """
    try:
        import platform
        import psutil
        import torch

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
        return JSONResponse(content={"error": f"システム情報の取得に失敗: {str(e)}"}, status_code=500)


if __name__ == "__main__":
    DEBUG = False
    if DEBUG:
        import uvicorn

        uvicorn.run(
            "src.api.core.patchcore_api:app",
            host=env_loader.API_SERVER_HOST,
            port=env_loader.API_SERVER_PORT,
            use_colors=False,
            workers=1,
            reload=True,
        )
