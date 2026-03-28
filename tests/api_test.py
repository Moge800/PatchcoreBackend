import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.api.client.patchcore_api_client import PatchCoreApiClient
from src.config import env_loader

MODEL_NAME = env_loader.DEFAULT_MODEL_NAME


def main():
    client = PatchCoreApiClient()
    print(f"{client.list_models()=}")
    print(f"{client.load_model(MODEL_NAME)=}")
    print(f"{client.model_status(MODEL_NAME)=}")
    print(f"{client.fetch_image_list(MODEL_NAME, limit=10)=}")
    print(f"{client.fetch_system_info()=}")
    print(f"{client.fetch_gpu_info()=}")
    print(f"{client.unload_model(MODEL_NAME)=}")
    print(f"{client.list_models()=}")


main()
