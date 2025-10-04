"""
パフォーマンステスト用スクリプト
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import statistics
import glob
import numpy as np
from src.api.client.patchcore_api_client import PatchCoreApiClient
from src.model.utils.inference_utils import load_image_unicode_path


def run_benchmark():
    client = PatchCoreApiClient()

    if not client.wait_for_server(max_wait=5):
        print("サーバーが起動していません")
        return

    # システム情報表示
    try:
        system_response = client.get("/system_info")
        gpu_response = client.get("/gpu_info")
        status_response = client.get("/status")

        print("=== システム情報 ===")

        if system_response.status_code == 200:
            system_info = system_response.json()
            print(f"プラットフォーム: {system_info.get('platform', 'N/A')}")
            print(f"CPU: {system_info.get('cpu_count', 'N/A')}コア")
            print(f"RAM: {system_info.get('memory_total', 'N/A')}")
            print(f"PyTorch: {system_info.get('pytorch_version', 'N/A')}")
        else:
            print("システム情報の取得に失敗")

        if gpu_response.status_code == 200:
            gpu_info = gpu_response.json()
            print(f"CUDA: {gpu_info.get('cuda_available', False)}")
            print(f"現在のデバイス: {gpu_info.get('current_device', 'N/A')}")
        else:
            print("GPU情報の取得に失敗")

        if status_response.status_code == 200:
            status_info = status_response.json()
            print(f"モデル: {status_info.get('model', 'N/A')}")
            print(f"キャッシュ画像数: {status_info.get('image_cache', 0)}")
        else:
            print("ステータス情報の取得に失敗")

    except Exception as e:
        print(f"情報取得時にエラー: {e}")

    print()

    # テスト画像の準備
    try:
        from src.config import env_loader

        MODEL_NAME = env_loader.DEFAULT_MODEL_NAME
        img_list_path = f"settings/models/{MODEL_NAME}/test_image/*.png"
        img_list = glob.glob(img_list_path)
    except Exception as e:
        print(f"設定読み込みエラー: {e}")
        return

    if len(img_list) == 0:
        print(f"テスト画像が見つかりません: {img_list_path}")
        return

    # ベンチマーク実行
    print("=== ベンチマーク開始 ===")
    print(f"テスト画像数: {len(img_list)}枚")

    times = []
    results = {"OK": 0, "NG": 0}
    errors = 0

    for i, img_path in enumerate(img_list):
        try:
            img = load_image_unicode_path(img_path)

            start_time = time.perf_counter()
            response = client.predict(img)
            end_time = time.perf_counter()

            process_time = end_time - start_time
            times.append(process_time)
            results[response["label"]] += 1

        except Exception as e:
            errors += 1
            print(f"\nエラー ({img_path}): {e}")
            continue

        if times:
            print(
                f"\r進行状況: {i+1}/{len(img_list)} | 平均: {statistics.mean(times):.3f}s | エラー: {errors}",
                end="",
            )
        else:
            print(f"\r進行状況: {i+1}/{len(img_list)} | エラー: {errors}", end="")

    if not times:
        print("\n\n処理可能な画像がありませんでした")
        return

    print("\n\n=== ベンチマーク結果 ===")
    print(f"総処理数: {len(times)}枚（エラー: {errors}枚）")
    print(f"総処理時間: {sum(times):.3f}秒")
    print(f"平均処理時間: {statistics.mean(times):.3f}秒")
    print(f"最大処理時間: {max(times):.3f}秒")
    print(f"最小処理時間: {min(times):.3f}秒")
    print(f"標準偏差: {statistics.stdev(times):.3f}秒")
    print(f"スループット: {len(times)/sum(times):.1f}枚/秒")
    print(f"判定結果: OK={results['OK']}枚, NG={results['NG']}枚")

    # パフォーマンス分析
    if len(times) > 1:
        sorted_times = sorted(times)
        p95_idx = int(len(sorted_times) * 0.95) - 1
        p99_idx = int(len(sorted_times) * 0.99) - 1
        p95 = sorted_times[max(0, p95_idx)]
        p99 = sorted_times[max(0, p99_idx)]

        print("\n=== パフォーマンス分析 ===")
        print(f"95%ile: {p95:.3f}秒")
        print(f"99%ile: {p99:.3f}秒")
        print(f"中央値: {statistics.median(times):.3f}秒")

        # 異常検知率
        ng_rate = (results["NG"] / len(times)) * 100
        print(f"異常検知率: {ng_rate:.1f}%")

    # GPU メモリ情報（利用可能な場合のみ）
    try:
        gpu_response = client.get("/gpu_info")
        if gpu_response.status_code == 200:
            gpu_info = gpu_response.json()
            if gpu_info.get("cuda_available", False):
                memory_info = gpu_info.get("memory", {})
                print(f"\nGPU メモリ: {memory_info}")
    except Exception:
        pass


if __name__ == "__main__":
    run_benchmark()
