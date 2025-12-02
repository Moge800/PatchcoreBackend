"""
PatchCore API クライアントモジュール

PatchCore APIサーバーとHTTP通信するためのクライアントクラスを提供します。
画像のアップロード、推論実行、結果取得などの機能を持ちます。
"""

import requests
import numpy as np
import time
from typing import Optional, Dict, Any
from src.api.utils.api_util import (
    convert_image_to_png_bytes,
    convert_png_bytes_to_ndarray,
    ApiUrlBuilder,
)


class PatchCoreApiClient:
    """
    PatchCore API クライアント

    APIサーバーとの通信を管理し、画像の異常検出、システム情報取得、
    キャッシュ管理などの機能を提供します。

    Attributes:
        base_url: APIサーバーのベースURL
        session: HTTPセッション（接続プーリング用）
        timeout: リクエストのタイムアウト時間（秒）
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 5) -> None:
        """
        APIクライアントを初期化

        Args:
            base_url: APIサーバーのベースURL。Noneの場合は環境変数から取得
            timeout: リクエストのタイムアウト時間（秒）

        Example:
            >>> client = PatchCoreApiClient("http://localhost:8000")
            >>> # または環境変数から自動取得
            >>> client = PatchCoreApiClient()
        """
        # base_urlが指定されていない場合は環境変数から取得
        if base_url is None:
            from src.config import env_loader

            base_url = (
                f"http://{env_loader.API_CLIENT_HOST}:{env_loader.API_CLIENT_PORT}"
            )

        self.base_url = base_url.rstrip("/")
        self.url_builder = ApiUrlBuilder(self.base_url)
        self.session = requests.Session()
        self.timeout = timeout

    def wait_for_server(self, endpoint: str = "/status", max_wait: int = 30) -> bool:
        """
        サーバーの起動を待機

        指定されたエンドポイントに定期的にアクセスし、サーバーが起動するまで待ちます。

        Args:
            endpoint: 確認するエンドポイント（デフォルト: "/status"）
            max_wait: 最大待機時間（秒）

        Returns:
            サーバーが起動した場合True、タイムアウトした場合False

        Example:
            >>> client = PatchCoreApiClient()
            >>> if client.wait_for_server(max_wait=60):
            ...     print("サーバーが起動しました")
        """
        url = self.url_builder.make(endpoint)
        for _ in range(max_wait * 2):
            try:
                response = self.session.get(url, timeout=0.5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                time.sleep(0.5)
        return False

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """
        汎用GETリクエスト

        Args:
            endpoint: リクエストするエンドポイント
            **kwargs: requests.get()に渡す追加パラメータ

        Returns:
            HTTPレスポンス
        """
        url = self.url_builder.make(endpoint)
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """
        汎用POSTリクエスト

        Args:
            endpoint: リクエストするエンドポイント
            **kwargs: requests.post()に渡す追加パラメータ

        Returns:
            HTTPレスポンス
        """
        url = self.url_builder.make(endpoint)
        return self.session.post(url, timeout=self.timeout, **kwargs)

    def fetch_status(self) -> Optional[Dict[str, Any]]:
        """
        サーバーのステータスを取得

        Returns:
            ステータス情報の辞書。エラー時はNone

        Example:
            >>> client = PatchCoreApiClient()
            >>> status = client.status()
            >>> print(status["model_name"])
        """
        url = self.url_builder.make("/status")
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"status: {e}")
            return None

    def restart_engine(self) -> Optional[Dict[str, Any]]:
        """
        推論エンジンを再起動

        設定ファイルの変更を反映させるために使用します。

        Returns:
            再起動結果の辞書。エラー時はNone
        """
        url = self.url_builder.make("/engine/restart")
        try:
            response = self.session.post(
                url, params={"execute": True}, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"restart_engine: {e}")
            return None

    def fetch_image_list(
        self,
        limit: int = 100,
        prefix: Optional[str] = None,
        label: Optional[str] = None,
        reverse_list: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        キャッシュされた画像のIDリストを取得

        Args:
            limit: 取得する最大件数
            prefix: フィルタ用プレフィックス（"org_" または "ovr_"）
            label: フィルタ用ラベル（"OK" または "NG"）
            reverse_list: Trueの場合、リストを逆順にする

        Returns:
            画像IDリストを含む辞書。エラー時はNone
        """
        url = self.url_builder.make("/images")
        params: Dict[str, Any] = {"limit": limit, "reverse_list": reverse_list}
        if prefix:
            params["prefix"] = prefix
        if label:
            params["label"] = label

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"fetch_image_list: {e}")
            return None

    def predict(
        self,
        image: np.ndarray,
        detail_level: str = "basic",
        retries: int = 3,
        retry_delay: float = 0.5,
    ) -> Optional[Dict[str, Any]]:
        """
        画像の異常検出推論を実行

        Args:
            image: 入力画像（NumPy配列、BGR形式）
            detail_level: 詳細レベル（"basic" または "full"）
            retries: 失敗時のリトライ回数
            retry_delay: リトライ間の待機時間（秒）

        Returns:
            推論結果の辞書（label, z_stats, image_id など）。エラー時はNone

        Example:
            >>> import cv2
            >>> client = PatchCoreApiClient()
            >>> img = cv2.imread("test.jpg")
            >>> result = client.predict(img, detail_level="full")
            >>> print(result["label"])  # "OK" or "NG"
        """
        url = self.url_builder.make("/engine/predict")
        image_bytes = convert_image_to_png_bytes(image)
        files = {"file": ("image.png", image_bytes, "image/png")}
        params = {"detail_level": detail_level}

        for attempt in range(1, retries + 1):
            try:
                response = self.session.post(
                    url, files=files, params=params, timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    print(f"リトライ {attempt}/{retries}: {e}")
                    time.sleep(retry_delay)
                else:
                    print(f"予測失敗: {e}")

        print("リトライ上限に達しました")
        return None

    def fetch_image(self, image_id: str) -> Optional[np.ndarray]:
        """
        IDから画像を取得

        Args:
            image_id: 取得する画像のID（"org_" または "ovr_" で始まる）

        Returns:
            画像配列（NumPy配列、BGR形式）。エラー時はNone

        Example:
            >>> client = PatchCoreApiClient()
            >>> img = client.get_image("org_NG_20250104120000_abc1")
            >>> cv2.imshow("Image", img)
        """
        url = self.url_builder.make(f"/images/{image_id}")
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return convert_png_bytes_to_ndarray(response.content)
        except requests.exceptions.RequestException as e:
            print(f"fetch_image: {e}")
            return None

    def fetch_gpu_info(self) -> Dict[str, Any]:
        """
        GPU情報を取得

        Returns:
            GPU情報を含む辞書（cuda_available, gpu_count, gpu_names など）
        """
        try:
            response = self.get("/gpu_info")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            return {"error": str(e)}

    def fetch_system_info(self) -> Dict[str, Any]:
        """
        システム情報を取得

        Returns:
            システム情報を含む辞書（python_version, platform, cpu_count など）
        """
        try:
            response = self.get("/system_info")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            return {"error": str(e)}

    def clear_image_cache(self, execute: bool = False) -> Dict[str, Any]:
        """
        画像キャッシュをクリア

        Args:
            execute: Trueの場合、実際にクリアを実行。Falseの場合は確認のみ

        Returns:
            クリア結果を含む辞書
        """
        try:
            response = self.post("/images/clear", params={"execute": execute})
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            return {"error": str(e)}
