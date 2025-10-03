# デバッグ用だよ
import time
import glob
import cv2
import numpy as np
from src.api.client.patchcore_api_client import PatchCoreApiClient
from src.model.utils.inference_utils import load_image_unicode_path
from src.config.settings_loader import SettingsLoader

client = PatchCoreApiClient()
if not client.wait_for_server(max_wait=3):
    print("サーバーが起動していません")
    exit(1)

settings = SettingsLoader("settings/main_settings.py")
MODEL_NAME = settings.get_variable("MODEL_NAME")
try:
    img_list_path = f"settings/models/{MODEL_NAME}/test_image/*.png"
    img_list = glob.glob(img_list_path)
except Exception:
    raise FileNotFoundError(f"img_listの取得に失敗したよ:{img_list_path}")
if len(img_list) == 0:
    raise ValueError(f"画像が0枚だよ:{img_list_path}")

tmp = []
for img_path in img_list:
    start = time.perf_counter()
    img = load_image_unicode_path(img_path)
    response = client.predict(img)
    end = time.perf_counter()
    ovr = client.get_image(response["image_id"]["overlay"])
    org = client.get_image(response["image_id"]["original"])
    if ovr is not None and org is not None:
        ovr = cv2.resize(ovr, [400, 400])
        org = cv2.resize(org, [400, 400])
        img = cv2.hconcat([org, ovr])
        color = (0, 255, 0) if response["label"] == "OK" else (0, 0, 255)
        cv2.putText(img, response["label"], (10, 390), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
        cv2.imshow("frame", img)
        cv2.waitKey(1)
    elapse = end - start
    print(f"\r{round(elapse,4)}", end="")
    tmp.append(elapse)
if img_list:
    print(f"\n{round(np.average(tmp),4)}")
    print(np.round(tmp, 4).tolist())

cv2.destroyAllWindows()
