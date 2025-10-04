"""
API ユーティリティモジュール

画像形式の変換、URL構築などのAPI関連ユーティリティ関数を提供します。
"""

import cv2
import numpy as np
from urllib.parse import urlparse


def convert_image_to_png_bytes(image: np.ndarray) -> bytes:
    """
    NumPy画像配列をPNGバイト列に変換

    HTTPリクエストで画像を送信する際に使用します。

    Args:
        image: 変換する画像配列（BGR形式）

    Returns:
        PNGフォーマットのバイト列

    Raises:
        ValueError: 画像のエンコードに失敗した場合

    Example:
        >>> img = cv2.imread("test.jpg")
        >>> png_bytes = convert_image_to_png_bytes(img)
        >>> print(len(png_bytes))
        12345
    """
    try:
        success, encoded_image = cv2.imencode(".png", image)
        if not success:
            raise ValueError("画像のエンコードに失敗しました")
        return encoded_image.tobytes()
    except Exception as e:
        raise ValueError(f"画像の変換エラー: {e}")


def convert_png_bytes_to_ndarray(image_bytes: bytes) -> np.ndarray:
    """
    PNGバイト列をNumPy画像配列に変換

    HTTPレスポンスから受信した画像データをデコードする際に使用します。

    Args:
        image_bytes: PNGフォーマットのバイト列

    Returns:
        デコードされた画像配列（BGR形式）

    Raises:
        ValueError: 画像のデコードに失敗した場合

    Example:
        >>> response = requests.get("http://api/get_image?id=123")
        >>> img = convert_png_bytes_to_ndarray(response.content)
        >>> cv2.imshow("Image", img)
    """
    try:
        image_bytes = np.frombuffer(image_bytes, dtype=np.uint8)
        image_array = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
        if image_array is None:
            raise ValueError("画像のデコードに失敗しました")
        return image_array
    except Exception as e:
        raise ValueError(f"画像の変換エラー: {e}")


def make_url(api_url: str, end_point: str) -> str:
    """
    ベースURLとエンドポイントを結合してフルURLを生成

    Args:
        api_url: ベースURL（末尾のスラッシュは自動削除）
        end_point: エンドポイント（先頭のスラッシュは自動削除）

    Returns:
        結合されたフルURL

    Example:
        >>> url = make_url("http://localhost:8000/", "/predict")
        >>> print(url)
        http://localhost:8000/predict
    """
    return f"{api_url.rstrip('/')}/{end_point.lstrip('/')}"


class ApiUrlBuilder:
    """
    API URLビルダー

    ベースURLを保持し、エンドポイントを追加してフルURLを生成します。
    URLの妥当性を検証し、一貫したURL構築を保証します。

    Attributes:
        _base_url: 検証済みのベースURL
    """

    def __init__(self, base_url: str) -> None:
        """
        URLビルダーを初期化

        Args:
            base_url: ベースURL（http:// または https:// で始まる必要がある）

        Raises:
            ValueError: URLが不正な場合

        Example:
            >>> builder = ApiUrlBuilder("http://localhost:8000")
            >>> url = builder.make("/status")
            >>> print(url)
            http://localhost:8000/status
        """
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"不正なURLです: {base_url}")
        self._base_url = base_url.rstrip("/")

    def make(self, endpoint: str) -> str:
        """
        エンドポイントを追加してフルURLを生成

        Args:
            endpoint: 追加するエンドポイント

        Returns:
            結合されたフルURL
        """
        return f"{self._base_url}/{endpoint.lstrip('/')}"
