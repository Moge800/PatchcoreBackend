"""
型定義モジュール

プロジェクト全体で使用する型エイリアスとTypedDictを定義します。
型安全性を向上させ、IDEの補完機能を活用できるようにします。
"""

from typing import TypedDict, Literal
import numpy as np
from numpy.typing import NDArray


# ===== 基本型エイリアス =====

ImageArray = NDArray[np.uint8]
"""画像配列型（NumPy配列、dtype=uint8）"""

DeviceType = Literal["cpu", "cuda"]
"""デバイス型（CPUまたはCUDA GPU）"""

LabelType = Literal["OK", "NG"]
"""判定結果型（正常または異常）"""

DetailLevel = Literal["basic", "full"]
"""API応答の詳細レベル（基本情報のみ、または全情報）"""


# ===== TypedDict定義 =====


class ZScoreStats(TypedDict):
    """
    Z-score統計情報

    画像の異常度を表すZ-scoreの統計値を格納します。

    Attributes:
        area: 異常領域の面積（ピクセル数）
        maxval: 最大Z-scoreの値
        mean: Z-scoreの平均値
        std: Z-scoreの標準偏差
    """

    area: float
    maxval: float
    mean: float
    std: float


class Thresholds(TypedDict):
    """
    異常検出しきい値設定

    異常判定に使用される各種しきい値を格納します。

    Attributes:
        z_score: Z-scoreの平均値しきい値
        z_area: 異常領域面積のしきい値（ピクセル数）
        z_max: 最大Z-scoreのしきい値
    """

    z_score: float
    z_area: float
    z_max: float


class ImageIds(TypedDict):
    """
    画像識別子

    保存された画像へのアクセスに使用するIDを格納します。

    Attributes:
        original: オリジナル画像のID（プレフィックス: "org_"）
        overlay: ヒートマップ重畳画像のID（プレフィックス: "ovr_"）
    """

    original: str
    overlay: str


class PredictionResult(TypedDict):
    """
    推論エンジンの予測結果

    内部の推論エンジンが返す完全な予測結果を格納します。

    Attributes:
        label: 判定結果（"OK" または "NG"）
        z_stats: Z-score統計情報
        thresholds: 使用されたしきい値
        image_id: 保存された画像のID
    """

    label: LabelType
    z_stats: ZScoreStats
    thresholds: Thresholds
    image_id: ImageIds


class APIResponse(TypedDict):
    """
    API エンドポイントの応答形式

    /predict エンドポイントが返すJSON応答の構造を定義します。

    Attributes:
        label: 判定結果（"OK" または "NG"）
        process_time: 処理時間（秒）
        image_id: 保存された画像のID
        thresholds: 使用されたしきい値
        z_stats: Z-score統計情報（detail_levelにより内容が変わる）
    """

    label: LabelType
    process_time: float
    image_id: ImageIds
    thresholds: Thresholds
    z_stats: ZScoreStats
