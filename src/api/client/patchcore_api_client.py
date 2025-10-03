import requests
import time
import numpy as np
from src.api.utils.api_util import convert_image_to_png_bytes, convert_png_bytes_to_ndarray, ApiUrlBuilder


class PatchCoreApiClient:
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.url_builder = ApiUrlBuilder(self.base_url)
        self.session = requests.Session()
        self.timeout = timeout

    def wait_for_server(self, endpoint: str = "/status", max_wait: int = 30) -> bool:
        url = self.url_builder.make(endpoint)
        for _ in range(max_wait * 2):
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return True
            except requests.exceptions.RequestException:
                time.sleep(0.5)
        return False

    def status(self):
        url = self.url_builder.make("/status")
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"status: {e}")
            return None

    def restart_engine(self):
        url = self.url_builder.make("/restart_engine")
        try:
            response = self.session.post(url, params={"execute": True}, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"restart_engine: {e}")
            return None

    def get_image_list(self, limit=100, prefix=None, label=None, reverse_list=False):
        url = self.url_builder.make("/get_image_list")
        params = {"limit": limit, "reverse_list": reverse_list}
        if prefix:
            params["prefix"] = prefix
        if label:
            params["label"] = label

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("image_list", [])
        except requests.exceptions.RequestException as e:
            print(f"get_image_list: {e}")
            return []

    def predict(self, image: np.ndarray, detail_level: str = "basic", retries: int = 3, retry_delay: float = 0.5):
        url = self.url_builder.make("/predict")
        image_bytes = convert_image_to_png_bytes(image)
        files = {"file": ("image.png", image_bytes, "image/png")}
        params = {"detail_level": detail_level}

        for attempt in range(1, retries + 1):
            try:
                response = self.session.post(url, files=files, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"[{attempt}/{retries}] Error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"[{attempt}/{retries}] Request failed: {e}")
            time.sleep(retry_delay)
        print("リトライ上限に達しました")
        return None

    def get_image(self, image_id: str):
        url = self.url_builder.make("/get_image")
        try:
            response = self.session.get(url, params={"image_id": image_id}, timeout=self.timeout)
            response.raise_for_status()
            return convert_png_bytes_to_ndarray(response.content)
        except requests.exceptions.RequestException as e:
            print(f"get_image: {e}")
            return None

    def clear_image_cache(self):
        url = self.url_builder.make("/clear_image")
        try:
            response = self.session.post(url, params={"execute": True}, timeout=self.timeout)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"clear_image_cache: {e}")
            return None
