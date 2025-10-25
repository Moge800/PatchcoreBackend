"""
API基本動作テスト
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import glob
import cv2
import numpy as np
from src.api.client.patchcore_api_client import PatchCoreApiClient
from src.model.utils.inference_utils import load_image_unicode_path


def main():
    client = PatchCoreApiClient()
    if not client.wait_for_server(max_wait=3):
        print("サーバーが起動していません")
        exit(1)

    # システム情報の取得
    try:
        system_info = client.get("/system_info").json()
        print(f"システム情報: {system_info['platform']}")
        print(f"CPU: {system_info['cpu_count']}コア, RAM: {system_info['memory_total']}")
        print(f"PyTorch: {system_info['pytorch_version']}, CUDA: {system_info['cuda_support']}")
    except Exception:
        print("システム情報の取得に失敗")

    from src.config import env_loader

    MODEL_NAME = env_loader.DEFAULT_MODEL_NAME
    try:
        img_list_path = f"settings/models/{MODEL_NAME}/test_image/*.png"
        img_list = glob.glob(img_list_path)
    except Exception:
        raise FileNotFoundError(f"img_listの取得に失敗したよ:{img_list_path}")
    if len(img_list) == 0:
        raise ValueError(f"画像が0枚だよ:{img_list_path}")

    print(f"\n処理開始: {len(img_list)}枚の画像")
    tmp = []
    ok_count = 0
    ng_count = 0
    ng_list = []

    for i, img_path in enumerate(img_list):
        start = time.perf_counter()
        img = load_image_unicode_path(img_path)

        # API呼び出し時間を測定
        api_start = time.perf_counter()
        response = client.predict(img)
        api_end = time.perf_counter()

        if response["label"] != "OK":
            ng_list.append(response["image_id"]["overlay"])

        # 画像取得時間を測定
        img_start = time.perf_counter()
        ovr = client.fetch_image(response["image_id"]["overlay"])
        org = client.fetch_image(response["image_id"]["original"])
        img_end = time.perf_counter()

        end = time.perf_counter()

        # 結果カウント
        if response["label"] == "OK":
            ok_count += 1
        else:
            ng_count += 1

        if ovr is not None and org is not None:
            ovr = cv2.resize(ovr, [400, 400])
            org = cv2.resize(org, [400, 400])
            img_display = cv2.hconcat([org, ovr])
            color = (0, 255, 0) if response["label"] == "OK" else (0, 0, 255)

            # ラベル表示
            cv2.putText(img_display, response["label"], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

            # 詳細情報表示
            cv2.putText(
                img_display,
                f"API: {api_end-api_start:.3f}s",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )
            cv2.putText(
                img_display,
                f"IMG: {img_end-img_start:.3f}s",
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )
            cv2.putText(
                img_display, f"Total: {end-start:.3f}s", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )

            # 進行状況表示
            cv2.putText(
                img_display, f"{i+1}/{len(img_list)}", (10, 390), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )

            cv2.imshow("frame", img_display)
            cv2.waitKey(1)

        elapse = end - start
        print(f"\r進行状況: {i+1}/{len(img_list)} | 時間: {elapse:.4f}s | OK: {ok_count} | NG: {ng_count}", end="")
        tmp.append(elapse)

    print("\n\n=== 結果サマリー ===")
    print(f"総処理数: {len(img_list)}枚")
    print(f"OK: {ok_count}枚, NG: {ng_count}枚")
    print(f"平均処理時間: {np.average(tmp):.4f}秒")
    print(f"最大処理時間: {np.max(tmp):.4f}秒")
    print(f"最小処理時間: {np.min(tmp):.4f}秒")
    print(f"処理時間の標準偏差: {np.std(tmp):.4f}秒")
    print(f"詳細: {np.round(tmp, 4).tolist()}")

    if len(ng_list) > 0:
        for i, ng in enumerate(ng_list):
            img = client.fetch_image(ng)
            if img is not None:
                cv2.putText(img, f"NG[{i}/{len(ng_list)}]", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                cv2.putText(
                    img, "Press any key to continue...", (10, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                )
                img = cv2.resize(img, [400, 400])
                cv2.imshow("NG image", img)
                cv2.waitKey(0)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
