"""
プロジェクト全体で使用する定数定義

ハードコードされたパスやマジックナンバーを一元管理します。
"""

from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent

# ディレクトリパス
DATASETS_DIR = PROJECT_ROOT / "datasets"
MODELS_DIR = PROJECT_ROOT / "models"
SETTINGS_DIR = PROJECT_ROOT / "settings"
LOGS_DIR = PROJECT_ROOT / "logs"

# サブディレクトリパス
SETTINGS_MODELS_DIR = SETTINGS_DIR / "models"

# ファイル名
SETTINGS_FILENAME = "settings.py"
MEMORY_BANK_FILENAME = "memory_bank.pkl"
MEMORY_BANK_COMPRESSED_FILENAME = "memory_bank_compressed.pkl"
PCA_FILENAME = "pca.pkl"
MODEL_FILENAME = "model.pt"
PIXEL_STATS_FILENAME = "pixel_stats.pkl"


# モデル関連のパスを生成するヘルパー関数
def get_model_dir(model_name: str) -> Path:
    """モデルディレクトリのパスを取得"""
    return MODELS_DIR / model_name


def get_settings_path(model_name: str) -> Path:
    """モデル設定ファイルのパスを取得"""
    return SETTINGS_MODELS_DIR / model_name / SETTINGS_FILENAME


def get_dataset_dir(model_name: str) -> Path:
    """データセットディレクトリのパスを取得"""
    return DATASETS_DIR / model_name


def get_normal_dir(model_name: str) -> Path:
    """正常画像ディレクトリのパスを取得"""
    return get_dataset_dir(model_name) / "normal"


def get_augmented_dir(model_name: str) -> Path:
    """拡張画像ディレクトリのパスを取得"""
    return get_dataset_dir(model_name) / "normal_augmented"


# 画像関連の定数
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")

# その他の定数
DEFAULT_SAMPLING_RATIO = 0.1
DEFAULT_LOG_INTERVAL = 10
