"""
デバイス管理ユーティリティモジュール

PyTorchのCPU/GPU選択とメモリ管理機能を提供します。
"""

import torch
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_device(use_gpu: bool = True, device_id: int = 0) -> torch.device:
    """
    使用するデバイスを取得する

    GPUの可用性を確認し、適切なデバイス（cuda:X または cpu）を返します。
    GPUが使用できない場合は自動的にCPUにフォールバックします。

    Args:
        use_gpu: Trueの場合、GPUの使用を試みる
        device_id: 使用するGPUのデバイスID（複数GPU環境で有効）

    Returns:
        選択されたデバイス（cuda:X または cpu）

    Example:
        >>> device = get_device(use_gpu=True, device_id=0)
        >>> print(device)
        cuda:0
    """
    if use_gpu and torch.cuda.is_available():
        if device_id < torch.cuda.device_count():
            device = torch.device(f"cuda:{device_id}")
            logger.info(f"GPU使用: {torch.cuda.get_device_name(device_id)}")
            return device
        else:
            logger.warning(
                f"指定されたGPU ID {device_id} が見つかりません。CPUを使用します。"
            )
    elif use_gpu:
        logger.info("CUDA が利用できません。CPUを使用します。")
    else:
        logger.info("CPU使用（設定によりGPUを無効化）")

    return torch.device("cpu")


def clear_gpu_cache() -> None:
    """
    GPU メモリキャッシュをクリアする

    PyTorchのメモリキャッシュを解放します。
    メモリ不足エラーを回避するために、推論後に呼び出すことを推奨します。
    ログ出力は行いません（パフォーマンス重視）。

    Note:
        CUDAが利用できない場合は何も行いません。
    """
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def get_gpu_memory_info() -> Dict[str, str]:
    """
    GPU メモリ使用状況を取得する

    現在の GPU メモリの割り当て量とキャッシュ量を返します。
    API のヘルスチェックエンドポイント等で使用します。

    Returns:
        メモリ使用状況を含む辞書
        - allocated: 割り当て済みメモリ量（GB単位の文字列）
        - cached: キャッシュされたメモリ量（GB単位の文字列）

        CPUモードの場合は両方とも "N/A (CPU mode)" を返します。

    Example:
        >>> info = get_gpu_memory_info()
        >>> print(info)
        {'allocated': '2.35GB', 'cached': '3.12GB'}
    """
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        cached = torch.cuda.memory_reserved() / 1e9
        return {"allocated": f"{allocated:.2f}GB", "cached": f"{cached:.2f}GB"}
    return {"allocated": "N/A (CPU mode)", "cached": "N/A (CPU mode)"}


def check_gpu_environment() -> Dict[str, Any]:
    """
    GPU環境の詳細情報を取得

    CUDA、PyTorch、GPU デバイスに関する包括的な情報を返します。
    デバッグやシステム診断に使用します。

    Returns:
        GPU環境情報を含む辞書
        - cuda_available: CUDAが利用可能かどうか
        - pytorch_version: PyTorchのバージョン
        - cuda_version: CUDAのバージョン（利用可能な場合）
        - gpu_count: 利用可能なGPU数（CUDAが利用可能な場合）
        - gpu_names: GPU名のリスト（CUDAが利用可能な場合）
        - reason: CUDAが利用できない理由（利用不可の場合）

    Example:
        >>> env = check_gpu_environment()
        >>> print(env)
        {
            'cuda_available': True,
            'pytorch_version': '2.6.0+cu124',
            'cuda_version': '12.4',
            'gpu_count': 1,
            'gpu_names': ['NVIDIA GeForce RTX 4090']
        }
    """
    info: Dict[str, Any] = {
        "cuda_available": torch.cuda.is_available(),
        "pytorch_version": torch.__version__,
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
    }

    if torch.cuda.is_available():
        info["gpu_count"] = torch.cuda.device_count()
        info["gpu_names"] = [
            torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
        ]
    else:
        info["reason"] = (
            "CUDA not available - check NVIDIA drivers and CUDA installation"
        )

    return info
