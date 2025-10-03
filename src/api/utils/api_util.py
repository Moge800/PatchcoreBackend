import cv2
import numpy as np
from urllib.parse import urlparse


def convert_image_to_png_bytes(image: np.ndarray) -> bytes:
    try:
        success, encoded_image = cv2.imencode(".png", image)
        if not success:
            raise ValueError("画像のエンコードに失敗しました")
        return encoded_image.tobytes()
    except Exception as e:
        raise ValueError(f"画像の変換エラー: {e}")


def convert_png_bytes_to_ndarray(image_bytes) -> np.ndarray:
    try:
        image_bytes = np.frombuffer(image_bytes, dtype=np.uint8)
        image_array = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if image_array is None:
            raise ValueError("画像のデコードに失敗しました")
        return image_array
    except Exception as e:
        raise ValueError(f"画像の変換エラー: {e}")


def make_url(api_url: str, end_point: str) -> str:
    return f"{api_url.rstrip('/')}/{end_point.lstrip('/')}"


class ApiUrlBuilder:
    def __init__(self, base_url: str):
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"不正なURLです: {base_url}")
        self._base_url = base_url.rstrip("/")

    def make(self, endpoint: str) -> str:
        return f"{self._base_url}/{endpoint.lstrip('/')}"
