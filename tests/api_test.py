import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.api.client.patchcore_api_client import PatchCoreApiClient


def main():
    client = PatchCoreApiClient()
    print(f"{client.status()=}")
    print(f"{client.get_image_list()=}")
    for i in client.get_image_list(1000)["image_list"]:
        _ = client.get_image(i)
    print(f"{client.get_system_info()=}")
    print(f"{client.get_gpu_info()=}")
    print(f"{client.restart_engine()=}")
    print(f"{client.status()=}")
    print(f"{client.get_image_list()=}")


main()
