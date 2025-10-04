import os
import torch
import numpy as np
import cv2
from PIL import Image
from src.utils.logger import get_logger
from src.types import ImageArray

logger = get_logger(__name__)


def load_image_unicode_path(path: str) -> np.ndarray:
    """
    Unicode パスに対応した画像読み込み

    Args:
        path (str): 画像ファイルパス

    Returns:
        np.ndarray: BGR形式の画像配列

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: 画像の読み込みに失敗した場合
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


def preprocess_cv2(image: np.ndarray, quad_pts: list[list[float]], output_size: tuple[int, int]) -> torch.Tensor:
    """
    指定された画像に対して射影変換を行い、モデル入力用のテンソルに変換する。

    Args:
        image (np.ndarray): 入力画像。
        quad_pts (list of list of float): 射影変換に使用する4点座標（左上→右上→右下→左下）。
        output_size (tuple of int): 出力画像サイズ（幅, 高さ）。

    Returns:
        torch.Tensor: 正規化された画像テンソル（形状: [1, C, H, W]）。
    """

    src_pts = np.array(quad_pts, dtype=np.float32)
    dst_pts = np.array(
        [[0, 0], [output_size[0], 0], [output_size[0], output_size[1]], [0, output_size[1]]], dtype=np.float32
    )
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(image, M, output_size)
    tensor = torch.from_numpy(warped.transpose(2, 0, 1)).float() / 255.0
    return tensor.unsqueeze(0)


def save_overlay_image(overlay, save_dir: str, index: int, label: str, image_path: str):
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{index:03}_{label}_{os.path.basename(image_path)}"
    save_path = os.path.join(save_dir, filename)
    try:
        success = cv2.imwrite(save_path, overlay)
        if not success:
            logger.error(f"Failed to save image: {save_path}")
    except Exception as e:
        logger.error(f"Image save error: {e}", exc_info=True)
