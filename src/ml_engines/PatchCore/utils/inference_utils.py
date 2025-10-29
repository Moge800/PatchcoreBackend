"""
推論ユーティリティモジュール

画像の読み込み、前処理、射影変換、保存などの推論関連機能を提供します。
"""

import os
import torch
import numpy as np
import cv2
from PIL import Image
from typing import List, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_image_unicode_path(path: str) -> np.ndarray:
    """
    Unicode パスに対応した画像読み込み

    日本語を含むパスでも正しく画像を読み込めるように、
    PILを経由してOpenCV形式に変換します。

    Args:
        path: 画像ファイルのパス

    Returns:
        BGR形式の画像配列（OpenCV標準形式）

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: 画像の読み込みに失敗した場合

    Example:
        >>> img = load_image_unicode_path("C:/画像/テスト.png")
        >>> print(img.shape)
        (480, 640, 3)
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"画像ファイルが見つかりません: {path}")

    try:
        pil_img = Image.open(path).convert("RGB")
        img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        if img_array is None or img_array.size == 0:
            raise ValueError(f"画像の読み込みに失敗しました: {path}")

        return img_array
    except FileNotFoundError:
        raise
    except Exception as e:
        raise ValueError(f"画像読み込みエラー ({path}): {str(e)}")


def preprocess_cv2(
    image: np.ndarray, quad_pts: List[List[float]], output_size: Tuple[int, int]
) -> torch.Tensor:
    """
    指定された画像に対して射影変換を行い、モデル入力用のテンソルに変換する

    4点の座標を使用して射影変換（Perspective Transform）を実行し、
    画像を正規化してPyTorchテンソル形式に変換します。

    Args:
        image: 入力画像（BGR形式のNumPy配列）
        quad_pts: 射影変換に使用する4点座標（左上→右上→右下→左下の順）
                  例: [[0, 0], [640, 0], [640, 480], [0, 480]]
        output_size: 出力画像サイズ（幅, 高さ）のタプル

    Returns:
        正規化された画像テンソル（形状: [1, C, H, W]、値域: [0.0, 1.0]）

    Example:
        >>> img = cv2.imread("test.jpg")
        >>> pts = [[100, 50], [540, 50], [540, 430], [100, 430]]
        >>> tensor = preprocess_cv2(img, pts, (256, 256))
        >>> print(tensor.shape)
        torch.Size([1, 3, 256, 256])
    """
    src_pts = np.array(quad_pts, dtype=np.float32)
    dst_pts = np.array(
        [
            [0, 0],
            [output_size[0], 0],
            [output_size[0], output_size[1]],
            [0, output_size[1]],
        ],
        dtype=np.float32,
    )
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, M, output_size)
    tensor = torch.from_numpy(warped.transpose(2, 0, 1)).float() / 255.0
    return tensor.unsqueeze(0)


def save_overlay_image(
    overlay: np.ndarray, save_dir: str, index: int, label: str, image_path: str
) -> None:
    """
    ヒートマップ重畳画像を保存する

    ファイル名は "{index:03}_{label}_{元のファイル名}" の形式になります。

    Args:
        overlay: ヒートマップが重畳された画像（BGR形式）
        save_dir: 保存先ディレクトリのパス
        index: ファイル名に使用するインデックス番号（3桁ゼロ埋め）
        label: 判定結果ラベル（"OK" または "NG"）
        image_path: 元の画像ファイルのパス（ファイル名の取得に使用）

    Note:
        保存に失敗した場合はログにエラーを出力しますが、例外は発生させません。

    Example:
        >>> save_overlay_image(overlay_img, "output", 1, "NG", "test.jpg")
        # "output/001_NG_test.jpg" として保存される
    """
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{index:03}_{label}_{os.path.basename(image_path)}"
    save_path = os.path.join(save_dir, filename)
    try:
        success = cv2.imwrite(save_path, overlay)
        if not success:
            logger.error(f"Failed to save image: {save_path}")
    except Exception as e:
        logger.error(f"Image save error: {e}", exc_info=True)
