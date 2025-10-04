"""
環境変数ローダーモジュール
.envファイルから環境変数を読み込み、型変換とデフォルト値を提供
"""

import os
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを読み込み
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"

# .envファイルが存在する場合のみ読み込む
if _env_path.exists():
    load_dotenv(_env_path)


def get_env(key: str, default: Any = None, cast_type: type = str) -> Any:
    """
    環境変数を取得し、型変換を行う

    Args:
        key (str): 環境変数名
        default (Any): デフォルト値
        cast_type (type): 変換する型

    Returns:
        Any: 環境変数の値（型変換済み）
    """
    value = os.getenv(key)

    if value is None:
        return default

    try:
        if cast_type == bool:
            # bool型の特殊処理
            return value.lower() in ("true", "1", "yes", "on")
        elif cast_type == int:
            return int(value)
        elif cast_type == float:
            return float(value)
        elif cast_type == str:
            return value
        else:
            return cast_type(value)
    except (ValueError, TypeError):
        return default


def get_env_list(key: str, default: Optional[list] = None, separator: str = ",") -> list:
    """
    カンマ区切りの環境変数をリストとして取得

    Args:
        key (str): 環境変数名
        default (Optional[list]): デフォルト値
        separator (str): 区切り文字

    Returns:
        list: 環境変数のリスト
    """
    value = os.getenv(key)

    if value is None:
        return default or []

    return [item.strip() for item in value.split(separator) if item.strip()]


# アプリケーション設定
APP_NAME = get_env("APP_NAME", "PatchCoreBackend")
APP_VERSION = get_env("APP_VERSION", "1.0.0")
DEBUG = get_env("DEBUG", False, bool)

# APIサーバー設定
API_HOST = get_env("API_HOST", "0.0.0.0")
API_PORT = get_env("API_PORT", 8000, int)
API_RELOAD = get_env("API_RELOAD", False, bool)
API_WORKERS = get_env("API_WORKERS", 1, int)

# モデル設定
DEFAULT_MODEL_NAME = get_env("DEFAULT_MODEL_NAME", "example_model")

# ログ設定
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
LOG_DIR = get_env("LOG_DIR", "logs")

# GPU設定
USE_GPU = get_env("USE_GPU", False, bool)
GPU_DEVICE_ID = get_env("GPU_DEVICE_ID", 0, int)
USE_MIXED_PRECISION = get_env("USE_MIXED_PRECISION", True, bool)

# CPU最適化設定
CPU_THREADS = get_env("CPU_THREADS", 4, int)
CPU_MEMORY_EFFICIENT = get_env("CPU_MEMORY_EFFICIENT", True, bool)

# データ設定
DATA_DIR = get_env("DATA_DIR", "datasets")
MODEL_DIR = get_env("MODEL_DIR", "models")
SETTINGS_DIR = get_env("SETTINGS_DIR", "settings")

# キャッシュ設定
MAX_CACHE_IMAGES = get_env("MAX_CACHE_IMAGES", 1200, int)
CACHE_TTL = get_env("CACHE_TTL", 3600, int)

# NG画像保存設定
NG_IMAGE_SAVE = get_env("NG_IMAGE_SAVE", True, bool)

# セキュリティ設定
API_KEY = get_env("API_KEY", "your-secret-api-key-here")
ALLOWED_ORIGINS = get_env_list("ALLOWED_ORIGINS", ["http://localhost:3000", "http://localhost:8000"])


def get_cpu_optimization() -> dict:
    """
    CPU最適化設定を辞書形式で取得

    Returns:
        dict: CPU最適化設定
    """
    return {
        "threads": CPU_THREADS,
        "memory_efficient": CPU_MEMORY_EFFICIENT,
    }


def print_config():
    """デバッグ用：読み込まれた設定を表示"""
    print("=== 環境変数設定 ===")
    print(f"APP_NAME: {APP_NAME}")
    print(f"DEBUG: {DEBUG}")
    print(f"API_HOST: {API_HOST}")
    print(f"API_PORT: {API_PORT}")
    print(f"DEFAULT_MODEL_NAME: {DEFAULT_MODEL_NAME}")
    print(f"USE_GPU: {USE_GPU}")
    print(f"GPU_DEVICE_ID: {GPU_DEVICE_ID}")
    print(f"LOG_LEVEL: {LOG_LEVEL}")
    print(f"MAX_CACHE_IMAGES: {MAX_CACHE_IMAGES}")
    print(f"NG_IMAGE_SAVE: {NG_IMAGE_SAVE}")
    print("=" * 30)


if __name__ == "__main__":
    print_config()
