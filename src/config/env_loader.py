"""
環境変数ローダーモジュール
.envファイルから環境変数を読み込み、型変換とデフォルト値を提供
"""

import os
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを読み込み
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"

# .envファイルが存在する場合のみ読み込む
if _env_path.exists():
    load_dotenv(_env_path)


class EnvLoader:
    """環境変数を型変換して読み込むクラス"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self._load_env()

    def _load_env(self):
        """環境変数ファイルを読み込む"""
        if not os.path.exists(self.env_file):
            print(f"[Warning] {self.env_file} が見つかりません")
            return

        with open(self.env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    def get(self, key: str, default: Any = None, cast_type: type = str) -> Any:
        """
        環境変数を取得して型変換する

        Args:
            key (str): 環境変数のキー
            default (Any): デフォルト値
            cast_type (type): 変換する型

        Returns:
            Any: 型変換された値
        """
        value = os.getenv(key, default)

        if value is None:
            return default

        try:
            if cast_type is bool:
                # boolの場合は特別処理
                if isinstance(value, bool):
                    return value
                return value.lower() in ("true", "1", "yes")
            elif cast_type is int:
                return int(value)
            elif cast_type is float:
                return float(value)
            elif cast_type is str:
                return str(value)
            else:
                return cast_type(value)
        except (ValueError, TypeError):
            print(f"[Warning] {key}の型変換に失敗しました。デフォルト値を使用します。")
            return default


env_loader = EnvLoader()

# アプリケーション設定
APP_NAME = env_loader.get("APP_NAME", "PatchCoreBackend")
APP_VERSION = env_loader.get("APP_VERSION", "1.0.0")
DEBUG = env_loader.get("DEBUG", False, bool)

# APIサーバー設定
# ===== API設定 =====
# サーバー設定（バインドアドレス）
API_SERVER_HOST = env_loader.get("API_SERVER_HOST", "0.0.0.0")
API_SERVER_PORT = env_loader.get("API_SERVER_PORT", 8000, int)

# クライアント設定（接続先アドレス）
API_CLIENT_HOST = env_loader.get("API_CLIENT_HOST", "127.0.0.1")
API_CLIENT_PORT = env_loader.get("API_CLIENT_PORT", 8000, int)

# 後方互換性のための旧変数名（非推奨）
API_HOST = API_CLIENT_HOST  # 旧名称、新コードではAPI_CLIENT_HOSTを使用
API_PORT = API_CLIENT_PORT  # 旧名称、新コードではAPI_CLIENT_PORTを使用

API_RELOAD = env_loader.get("API_RELOAD", False, bool)
API_WORKERS = env_loader.get("API_WORKERS", 1, int)

# モデル設定
DEFAULT_MODEL_NAME = env_loader.get("DEFAULT_MODEL_NAME", "example_model")

# ログ設定
LOG_LEVEL = env_loader.get("LOG_LEVEL", "INFO")
LOG_DIR = env_loader.get("LOG_DIR", "logs")

# GPU設定
USE_GPU = env_loader.get("USE_GPU", False, bool)
GPU_DEVICE_ID = env_loader.get("GPU_DEVICE_ID", 0, int)
USE_MIXED_PRECISION = env_loader.get("USE_MIXED_PRECISION", True, bool)

# CPU最適化設定
CPU_THREADS = env_loader.get("CPU_THREADS", 4, int)
CPU_MEMORY_EFFICIENT = env_loader.get("CPU_MEMORY_EFFICIENT", True, bool)

# データ設定
DATA_DIR = env_loader.get("DATA_DIR", "datasets")
MODEL_DIR = env_loader.get("MODEL_DIR", "models")
SETTINGS_DIR = env_loader.get("SETTINGS_DIR", "settings")

# キャッシュ設定
MAX_CACHE_IMAGES = env_loader.get("MAX_CACHE_IMAGES", 1200, int)
CACHE_TTL = env_loader.get("CACHE_TTL", 3600, int)

# NG画像保存設定
NG_IMAGE_SAVE = env_loader.get("NG_IMAGE_SAVE", True, bool)

# セキュリティ設定
API_KEY = env_loader.get("API_KEY", "your-secret-api-key-here")
ALLOWED_ORIGINS = env_loader.get("ALLOWED_ORIGINS", ["http://localhost:3000", "http://localhost:8000"], list)


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
