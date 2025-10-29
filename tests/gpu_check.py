"""
GPU動作確認スクリプト
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch
from src.config.settings_loader import SettingsLoader
from src.ml_engines.PatchCore.utils.device_utils import check_gpu_environment


def main():
    # GPU環境チェック
    env_info = check_gpu_environment()
    print("=== GPU環境情報 ===")
    for key, value in env_info.items():
        print(f"{key}: {value}")

    # 設定確認
    settings = SettingsLoader("settings/models/example_model/settings.py")
    print("\n=== モデル設定 ===")
    print(f"USE_GPU: {settings.get_variable('USE_GPU')}")
    print(f"GPU_DEVICE_ID: {settings.get_variable('GPU_DEVICE_ID')}")
    print(f"USE_MIXED_PRECISION: {settings.get_variable('USE_MIXED_PRECISION')}")

    # 簡易テスト
    if torch.cuda.is_available():
        print("\n=== GPU動作テスト ===")
        device = torch.device("cuda:0")
        x = torch.randn(1000, 1000, device=device)
        y = torch.randn(1000, 1000, device=device)

        import time

        start = time.perf_counter()
        z = torch.matmul(x, y)
        torch.cuda.synchronize()
        end = time.perf_counter()

        print(f"行列乗算テスト: {(end-start)*1000:.2f}ms")
        print(f"結果デバイス: {z.device}")
        print(f"GPU メモリ使用量: {torch.cuda.memory_allocated()/1e9:.3f}GB")

        # CPU比較
        print("\n=== CPU比較テスト ===")
        x_cpu = torch.randn(1000, 1000)
        y_cpu = torch.randn(1000, 1000)

        start = time.perf_counter()
        z_cpu = torch.matmul(x_cpu, y_cpu)
        end = time.perf_counter()

        print(f"行列乗算テスト (CPU): {(end-start)*1000:.2f}ms")
    else:
        print("\n❌ CUDAが利用できません")


if __name__ == "__main__":
    main()
