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
    """モデルディレクトリのパスを取得

    指定されたモデル名に対応するディレクトリパスを返します。
    モデルファイル（.pt）、メモリバンク、PCAなどが格納されるルートディレクトリです。

    Args:
        model_name: モデル名（例: "example_model"）

    Returns:
        モデルディレクトリの絶対パス（Pathオブジェクト）

    Example:
        >>> get_model_dir("example_model")
        WindowsPath('C:/Project/models/example_model')
    """
    return MODELS_DIR / model_name


def get_settings_path(model_name: str) -> Path:
    """モデル設定ファイルのパスを取得

    各モデル固有のsettings.pyファイルのパスを返します。
    このファイルには画像サイズ、しきい値、アフィン変換座標などが定義されます。

    Args:
        model_name: モデル名（例: "example_model"）

    Returns:
        settings.pyファイルの絶対パス（Pathオブジェクト）

    Example:
        >>> get_settings_path("example_model")
        WindowsPath('C:/Project/settings/models/example_model/settings.py')
    """
    return SETTINGS_MODELS_DIR / model_name / SETTINGS_FILENAME


def get_dataset_dir(model_name: str) -> Path:
    """データセットディレクトリのパスを取得

    学習用画像データが格納されるルートディレクトリのパスを返します。
    通常、この下に "normal" ディレクトリが配置されます。

    Args:
        model_name: モデル名（例: "example_model"）

    Returns:
        データセットディレクトリの絶対パス（Pathオブジェクト）

    Example:
        >>> get_dataset_dir("example_model")
        WindowsPath('C:/Project/datasets/example_model')
    """
    return DATASETS_DIR / model_name


def get_normal_dir(model_name: str) -> Path:
    """正常画像ディレクトリのパスを取得

    PatchCoreの学習に使用する正常画像が格納されるディレクトリのパスを返します。
    このディレクトリ内の画像から特徴量を抽出し、メモリバンクを生成します。

    Args:
        model_name: モデル名（例: "example_model"）

    Returns:
        正常画像ディレクトリの絶対パス（Pathオブジェクト）

    Example:
        >>> get_normal_dir("example_model")
        WindowsPath('C:/Project/datasets/example_model/normal')
    """
    return get_dataset_dir(model_name) / "normal"


def get_augmented_dir(model_name: str) -> Path:
    """拡張画像ディレクトリのパスを取得"""
    return get_dataset_dir(model_name) / "normal_augmented"


# 画像関連の定数
SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")

# その他の定数
DEFAULT_SAMPLING_RATIO = 0.1
DEFAULT_LOG_INTERVAL = 10
