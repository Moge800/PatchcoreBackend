"""
型定義モジュール
プロジェクト全体で使用する型エイリアスを定義
"""

from typing import TypedDict, Literal
import numpy as np
from numpy.typing import NDArray


# 画像型
ImageArray = NDArray[np.uint8]

# デバイス型
DeviceType = Literal["cpu", "cuda"]

# 判定結果型
LabelType = Literal["OK", "NG"]

# 詳細レベル型
DetailLevel = Literal["basic", "full"]


class ZScoreStats(TypedDict):
    """Zスコア統計情報"""

    area: float
    maxval: float
    mean: float
    std: float


class Thresholds(TypedDict):
    """しきい値設定"""

    z_score: float
    z_area: float
    z_max: float


class ImageIds(TypedDict):
    """画像ID"""

    original: str
    overlay: str


class PredictionResult(TypedDict):
    """推論結果"""

    label: LabelType
    z_stats: ZScoreStats
    thresholds: Thresholds
    image_id: ImageIds


class APIResponse(TypedDict):
    """API レスポンス"""

    label: LabelType
    process_time: float
    image_id: ImageIds
    thresholds: Thresholds
    z_stats: ZScoreStats
