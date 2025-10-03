import torch
import logging

logger = logging.getLogger(__name__)


def get_device(use_gpu: bool = True, device_id: int = 0) -> torch.device:
    """
    使用するデバイスを取得する

    Args:
        use_gpu (bool): GPUを使用するかどうか
        device_id (int): GPUデバイスID

    Returns:
        torch.device: 使用するデバイス
    """
    if use_gpu and torch.cuda.is_available():
        if device_id < torch.cuda.device_count():
            device = torch.device(f"cuda:{device_id}")
            logger.info(f"GPU使用: {torch.cuda.get_device_name(device_id)}")
            return device
        else:
            logger.warning(f"指定されたGPU ID {device_id} が見つかりません。CPUを使用します。")
    elif use_gpu:
        logger.info("CUDA が利用できません。CPUを使用します。")
    else:
        logger.info("CPU使用（設定によりGPUを無効化）")

    return torch.device("cpu")


def clear_gpu_cache():
    """GPU メモリキャッシュをクリアする（ログ出力なし）"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def get_gpu_memory_info():
    """GPU メモリ使用状況を取得する（API専用）"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        cached = torch.cuda.memory_reserved() / 1e9
        return {"allocated": f"{allocated:.2f}GB", "cached": f"{cached:.2f}GB"}
    return {"allocated": "N/A (CPU mode)", "cached": "N/A (CPU mode)"}


def check_gpu_environment():
    """GPU環境の詳細情報を取得"""
    info = {
        "cuda_available": torch.cuda.is_available(),
        "pytorch_version": torch.__version__,
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
    }

    if torch.cuda.is_available():
        info["gpu_count"] = torch.cuda.device_count()
        info["gpu_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    else:
        info["reason"] = "CUDA not available - check NVIDIA drivers and CUDA installation"

    return info
