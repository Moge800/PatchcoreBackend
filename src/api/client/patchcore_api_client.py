"""
PatchCore API クライアントモジュール

PatchCore APIサーバーとHTTP通信するためのクライアントクラスを提供します。
"""

import time
from typing import Any, Dict, List, Optional

import numpy as np
import requests

from src.api.utils.api_util import (
    ApiUrlBuilder,
    convert_image_to_png_bytes,
    convert_png_bytes_to_ndarray,
)


class PatchCoreApiClient:
    """
    PatchCore API クライアント

    Attributes:
        base_url: APIサーバーのベースURL
        session: HTTPセッション（接続プーリング用）
        timeout: リクエストのタイムアウト時間（秒）
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = 5) -> None:
        if base_url is None:
            from src.config import env_loader
            base_url = f"http://{env_loader.API_CLIENT_HOST}:{env_loader.API_CLIENT_PORT}"

        self.base_url = base_url.rstrip("/")
        self.url_builder = ApiUrlBuilder(self.base_url)
        self.session = requests.Session()
        self.timeout = timeout

    def wait_for_server(self, max_wait: int = 30) -> bool:
        """サーバーの起動を待機する"""
        url = self.url_builder.make("/system_info")
        for _ in range(max_wait * 2):
            try:
                response = self.session.get(url, timeout=0.5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                time.sleep(0.5)
        return False

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        url = self.url_builder.make(endpoint)
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        url = self.url_builder.make(endpoint)
        return self.session.post(url, timeout=self.timeout, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        url = self.url_builder.make(endpoint)
        return self.session.delete(url, timeout=self.timeout, **kwargs)

    # ===== モデル管理 =====

    def list_models(self) -> Optional[Dict[str, Any]]:
        """全モデルの一覧とロード状態を取得する"""
        try:
            response = self.get("/models")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"list_models: {e}")
            return None

    def load_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """モデルをメモリにロードする"""
        try:
            response = self.post(f"/models/{model_name}/load")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"load_model: {e}")
            return None

    def unload_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """モデルをメモリからアンロードする"""
        try:
            response = self.delete(f"/models/{model_name}/unload")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"unload_model: {e}")
            return None

    def model_status(self, model_name: str) -> Optional[Dict[str, Any]]:
        """特定モデルのステータスを取得する"""
        try:
            response = self.get(f"/models/{model_name}/status")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"model_status: {e}")
            return None

    # ===== 推論（ジョブキュー） =====

    def submit_predict(
        self,
        model_name: str,
        image: np.ndarray,
        detail_level: str = "basic",
    ) -> Optional[str]:
        """
        推論ジョブをキューに投入し job_id を返す。

        結果取得は `poll_job()` でポーリングしてください。
        """
        image_bytes = convert_image_to_png_bytes(image)
        files = {"file": ("image.png", image_bytes, "image/png")}
        params = {"detail_level": detail_level}
        try:
            response = self.post(
                f"/models/{model_name}/predict", files=files, params=params
            )
            response.raise_for_status()
            return response.json().get("job_id")  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"submit_predict: {e}")
            return None

    def poll_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """ジョブの状態と結果を取得する"""
        try:
            response = self.get(f"/jobs/{job_id}")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"poll_job: {e}")
            return None

    def predict(
        self,
        model_name: str,
        image: np.ndarray,
        detail_level: str = "basic",
        poll_interval: float = 0.2,
        poll_timeout: float = 60.0,
    ) -> Optional[Dict[str, Any]]:
        """
        推論を実行し結果が出るまでポーリングして返す（同期ラッパー）。

        Args:
            model_name: 推論に使うモデル名
            image: 入力画像（BGR NumPy配列）
            detail_level: "basic" または "full"
            poll_interval: ポーリング間隔（秒）
            poll_timeout: タイムアウト（秒）

        Returns:
            推論結果の辞書。エラー時は None
        """
        job_id = self.submit_predict(model_name, image, detail_level)
        if job_id is None:
            return None

        deadline = time.monotonic() + poll_timeout
        while time.monotonic() < deadline:
            job = self.poll_job(job_id)
            if job is None:
                return None
            status = job.get("status")
            if status == "completed":
                return job.get("result")
            if status == "failed":
                print(f"predict failed: {job.get('error')}")
                return None
            time.sleep(poll_interval)

        print(f"predict timeout after {poll_timeout}s")
        return None

    def list_jobs(
        self,
        model_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Optional[List[Dict[str, Any]]]:
        """ジョブ一覧を取得する"""
        params: Dict[str, Any] = {"limit": limit}
        if model_name:
            params["model_name"] = model_name
        if status:
            params["status"] = status
        try:
            response = self.get("/jobs", params=params)
            response.raise_for_status()
            return response.json().get("jobs")  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"list_jobs: {e}")
            return None

    # ===== 画像キャッシュ =====

    def fetch_image_list(
        self,
        model_name: str,
        limit: int = 100,
        prefix: Optional[str] = None,
        label: Optional[str] = None,
        reverse_list: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """モデルのキャッシュ画像 ID 一覧を取得する"""
        params: Dict[str, Any] = {"limit": limit, "reverse_list": reverse_list}
        if prefix:
            params["prefix"] = prefix
        if label:
            params["label"] = label
        try:
            response = self.get(f"/models/{model_name}/images", params=params)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except requests.exceptions.RequestException as e:
            print(f"fetch_image_list: {e}")
            return None

    def fetch_image(self, model_name: str, image_id: str) -> Optional[np.ndarray]:
        """キャッシュされた画像を取得する"""
        try:
            response = self.get(f"/models/{model_name}/images/{image_id}")
            response.raise_for_status()
            return convert_png_bytes_to_ndarray(response.content)
        except requests.exceptions.RequestException as e:
            print(f"fetch_image: {e}")
            return None

    def clear_image_cache(self, model_name: str, execute: bool = False) -> Dict[str, Any]:
        """モデルの画像キャッシュをクリアする"""
        try:
            response = self.post(
                f"/models/{model_name}/images/clear", params={"execute": execute}
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            return {"error": str(e)}

    # ===== システム情報 =====

    def fetch_gpu_info(self) -> Dict[str, Any]:
        """GPU 情報を取得する"""
        try:
            response = self.get("/gpu_info")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            return {"error": str(e)}

    def fetch_system_info(self) -> Dict[str, Any]:
        """システム情報を取得する"""
        try:
            response = self.get("/system_info")
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except Exception as e:
            return {"error": str(e)}
