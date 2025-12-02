"""
環境変数ローダーモジュール

.envファイルから環境変数を読み込み、型変換とデフォルト値を提供します。
プロジェクトルートの.envファイルを自動的に読み込みます。
"""

import os
from pathlib import Path
from typing import Any, TypeVar, Type, Dict, List, Union, overload, Optional
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを読み込み
_project_root = Path(__file__).parent.parent.parent
_env_path = _project_root / ".env"


def env_exists() -> bool:
    """
    .envファイルが存在するか確認

    Returns:
        .envファイルが存在する場合はTrue、存在しない場合はFalse
    """
    return _env_path.exists()


def make_env_file() -> None:
    """
    デフォルトの.envファイルを作成

    既に.envファイルが存在する場合は上書きしません。
    """
    if env_exists():
        print(f"[Info] {_env_path} は既に存在します。上書きしません。")
        return

    env_example_path = _env_path.parent / ".env.example"
    if env_example_path.exists():
        with open(env_example_path, "r", encoding="utf-8") as src, open(
            _env_path, "w", encoding="utf-8"
        ) as dst:
            dst.write(src.read())
        print(f"[Info] {_env_path} を {env_example_path} から作成しました。")
    else:
        print(
            f"[Error] {env_example_path} が見つかりません。デフォルトの.envファイルを作成できません。"
        )


# .envファイルがなければ作成し、読み込む
if not env_exists():
    make_env_file()
    load_dotenv(_env_path)
else:
    load_dotenv(_env_path)

T = TypeVar("T")


class EnvLoader:
    """
    環境変数を型変換して読み込むクラス

    .envファイルから環境変数を読み込み、指定された型への変換を行います。
    変換に失敗した場合はデフォルト値を返します。
    """

    def __init__(self, env_file: str = ".env") -> None:
        """
        EnvLoaderを初期化

        Args:
            env_file: 環境変数ファイルのパス（デフォルト: ".env"）
        """
        self.env_file = env_file
        self._load_env()

    def _load_env(self) -> None:
        """
        環境変数ファイルを読み込む

        ファイルが見つからない場合は警告を表示します。
        """
        if not os.path.exists(self.env_file):
            print(f"[Warning] {self.env_file} が見つかりません")
            return

        with open(self.env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    def get(self, key: str, default: Any = None, cast_type: Type[Any] = str) -> Any:  # type: ignore[assignment]
        """
        環境変数を取得して型変換する

        環境変数から値を取得し、指定された型に変換します。
        変換に失敗した場合はデフォルト値を返します。

        Args:
            key: 環境変数のキー名
            default: 変数が存在しない、または変換に失敗した場合のデフォルト値
            cast_type: 変換先の型（bool, int, float, str など）

        Returns:
            型変換された環境変数の値、または変換失敗時はデフォルト値

        Example:
            >>> loader = EnvLoader()
            >>> port = loader.get("API_PORT", 8000, int)
            >>> debug = loader.get("DEBUG", False, bool)
        """
        value = os.getenv(key, default)

        if value is None:
            return default

        try:
            if cast_type is bool:
                # boolの場合は特別処理(文字列"true"/"1"/"yes"を真と判定)
                if isinstance(value, bool):
                    return value  # type: ignore[return-value]
                return value.lower() in ("true", "1", "yes")  # type: ignore[return-value, union-attr]
            elif cast_type is int:
                return int(value)  # type: ignore[return-value, arg-type]
            elif cast_type is float:
                return float(value)  # type: ignore[return-value, arg-type]
            elif cast_type is str:
                return str(value)  # type: ignore[return-value]
            else:
                return cast_type(value)  # type: ignore[return-value]
        except (ValueError, TypeError):
            print(f"[Warning] {key}の型変換に失敗しました。デフォルト値を使用します。")
            return default


env_loader = EnvLoader()

# ===== アプリケーション設定 =====
APP_NAME: str = env_loader.get("APP_NAME", "PatchCoreBackend")
APP_VERSION: str = env_loader.get("APP_VERSION", "1.0.0")
DEBUG: bool = env_loader.get("DEBUG", False, bool)

# ===== API設定 =====
# サーバー設定（バインドアドレス - サーバーがリッスンするアドレス）
API_SERVER_HOST: str = env_loader.get("API_SERVER_HOST", "0.0.0.0")
API_SERVER_PORT: int = env_loader.get("API_SERVER_PORT", 8000, int)

# クライアント設定（接続先アドレス - クライアントが接続するアドレス）
API_CLIENT_HOST: str = env_loader.get("API_CLIENT_HOST", "127.0.0.1")
API_CLIENT_PORT: int = env_loader.get("API_CLIENT_PORT", 8000, int)

# 後方互換性のための旧変数名（非推奨、新コードではAPI_CLIENT_*を使用）
API_HOST: str = API_CLIENT_HOST
API_PORT: int = API_CLIENT_PORT

API_RELOAD: bool = env_loader.get("API_RELOAD", False, bool)
API_WORKERS: int = env_loader.get("API_WORKERS", 1, int)

# ===== モデル設定 =====
DEFAULT_MODEL_NAME: str = env_loader.get("DEFAULT_MODEL_NAME", "example_model")

# ===== ログ設定 =====
LOG_LEVEL: str = env_loader.get("LOG_LEVEL", "INFO")
LOG_DIR: str = env_loader.get("LOG_DIR", "logs")

# ===== GPU設定 =====
USE_GPU: bool = env_loader.get("USE_GPU", False, bool)
GPU_DEVICE_ID: int = env_loader.get("GPU_DEVICE_ID", 0, int)
USE_MIXED_PRECISION: bool = env_loader.get("USE_MIXED_PRECISION", True, bool)

# ===== CPU最適化設定 =====
CPU_THREADS: int = env_loader.get("CPU_THREADS", 4, int)
CPU_MEMORY_EFFICIENT: bool = env_loader.get("CPU_MEMORY_EFFICIENT", True, bool)

# ===== データ設定 =====
DATA_DIR: str = env_loader.get("DATA_DIR", "datasets")
MODEL_DIR: str = env_loader.get("MODEL_DIR", "models")
SETTINGS_DIR: str = env_loader.get("SETTINGS_DIR", "settings")

# ===== キャッシュ設定 =====
MAX_CACHE_IMAGES: int = env_loader.get("MAX_CACHE_IMAGES", 1200, int)
CACHE_TTL: int = env_loader.get("CACHE_TTL", 3600, int)

# ===== NG画像保存設定 =====
NG_IMAGE_SAVE: bool = env_loader.get("NG_IMAGE_SAVE", True, bool)

# ===== セキュリティ設定 =====
API_KEY: str = env_loader.get("API_KEY", "your-secret-api-key-here")
ALLOWED_ORIGINS: List[str] = env_loader.get(  # type: ignore[assignment]
    "ALLOWED_ORIGINS", ["http://localhost:3000", "http://localhost:8000"], list
)


def get_cpu_optimization() -> Dict[str, Any]:
    """
    CPU最適化設定を辞書形式で取得

    CPU実行時のパフォーマンス設定を返します。

    Returns:
        CPU最適化設定を含む辞書
        - threads: 使用するCPUスレッド数
        - memory_efficient: メモリ効率化モードの有効/無効

    Example:
        >>> config = get_cpu_optimization()
        >>> print(config["threads"])
        4
    """
    return {
        "threads": CPU_THREADS,
        "memory_efficient": CPU_MEMORY_EFFICIENT,
    }


def print_config() -> None:
    """
    デバッグ用：読み込まれた設定を表示

    主要な環境変数設定をコンソールに出力します。
    """
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
