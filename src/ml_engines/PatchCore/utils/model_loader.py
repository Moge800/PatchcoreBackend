"""モデル読み込みユーティリティモジュール

PatchCoreモデルと関連アセット（メモリバンク、PCA、統計情報）の読み込み機能を提供します。
"""

import os
import torch
import pickle
from typing import Tuple, Any
import numpy as np


def load_model_and_assets(
    model_dir: str, save_format: str
) -> Tuple[torch.nn.Module, np.ndarray, Any, np.ndarray, np.ndarray]:
    """モデルと学習済みアセットを読み込む

    指定されたディレクトリからPatchCoreモデルと関連ファイルを読み込みます。
    メモリバンクはsave_formatに応じて圧縮版または非圧縮版を選択します。

    Args:
        model_dir: モデルファイルが格納されたディレクトリパス
        save_format: メモリバンクの保存形式
                     - "compressed": PCA圧縮版（memory_bank_compressed.pkl）
                     - その他: 非圧縮版（memory_bank.pkl）

    Returns:
        読み込まれたアセットのタプル:
        - model: TorchScript形式のPatchCoreモデル（評価モード）
        - memory_bank: 特徴ベクトルのメモリバンク（NumPy配列）
        - pca: 次元削減用のPCA変換器（sklearn.decomposition.PCA）
        - pixel_mean: ピクセル値の平均値（正規化用）
        - pixel_std: ピクセル値の標準偏差（正規化用）

    Raises:
        FileNotFoundError: 必要なファイルが存在しない場合
        RuntimeError: モデルの読み込みに失敗した場合

    Example:
        >>> model, bank, pca, mean, std = load_model_and_assets(
        ...     "models/example_model", "compressed"
        ... )
        >>> print(model)
        RecursiveScriptModule(...)

    Note:
        - モデルは自動的に評価モード（eval()）に設定されます
        - 圧縮版メモリバンクはメモリ使用量を大幅に削減します（推奨）
    """
    model = torch.jit.load(os.path.join(model_dir, "model.pt"))
    model.eval()

    bank_path = (
        "memory_bank_compressed.pkl"
        if save_format == "compressed"
        else "memory_bank.pkl"
    )
    with open(os.path.join(model_dir, bank_path), "rb") as f:
        memory_bank = pickle.load(f)
    with open(os.path.join(model_dir, "pca.pkl"), "rb") as f:
        pca = pickle.load(f)
    with open(os.path.join(model_dir, "pixel_stats.pkl"), "rb") as f:
        pixel_mean, pixel_std = pickle.load(f)

    return model, memory_bank, pca, pixel_mean, pixel_std
