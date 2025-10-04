"""
推論エンジンモジュール

PatchCore モデルを使用した異常検出推論を実行します。
シングルトンパターンでインスタンスを管理し、画像のキャッシュ、GPU最適化、
非同期NG画像保存などの機能を提供します。
"""

import os
import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Optional
import numpy as np
import cv2
import threading
import torch
from sklearn.decomposition import PCA  # noqa: F401
from src.config.settings_loader import SettingsLoader
from src.model.utils.model_loader import load_model_and_assets
from src.model.utils.inference_utils import preprocess_cv2
from src.model.utils.score_utils import evaluate_z_score_map, is_ok_z
from src.model.utils.device_utils import get_device, clear_gpu_cache
from src.utils.logger import setup_logger
from src.types import PredictionResult, LabelType


class PatchCoreInferenceEngine:
    """
    PatchCore 異常検出推論エンジン

    シングルトンパターンで実装され、モデルごとに1つのインスタンスのみが存在します。
    画像の前処理、推論、後処理、結果の可視化を行います。

    Attributes:
        model_name: モデル名
        device: PyTorchデバイス（cuda:X または cpu）
        use_gpu: GPU使用フラグ
        use_mixed_precision: 混合精度計算の使用フラグ
        image_store: 画像キャッシュ（OrderedDict）
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """シングルトンインスタンスを返す"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str) -> None:
        """
        推論エンジンを初期化

        モデルとアセット（メモリバンク、PCA、統計情報）を読み込み、
        設定ファイルからパラメータを取得します。

        Args:
            model_name: 使用するモデルの名前（modelsディレクトリ内のフォルダ名）

        Note:
            シングルトンパターンのため、同じmodel_nameで複数回呼ばれても
            最初の初期化のみが実行されます。
        """
        if self._initialized:
            return
        self._initialized = True

        # ロガー初期化
        self.logger = setup_logger(f"inference_engine_{model_name}", log_dir="logs/inference")

        self.model_name = model_name
        self.model_dir = os.path.join("models", model_name)
        self.settings_dir = os.path.join("settings", "models", model_name)
        self.settings_path = os.path.join(self.settings_dir, "settings.py")

        self.loader = SettingsLoader(self.settings_path)
        self._reload_settings()

        # GPU設定
        self.use_gpu = self.loader.get_variable("USE_GPU")
        self.device_id = self.loader.get_variable("GPU_DEVICE_ID")
        self.use_mixed_precision = self.loader.get_variable("USE_MIXED_PRECISION")
        self.device = get_device(self.use_gpu, self.device_id)

        self.model, self.memory_bank, self.pca, self.pixel_mean, self.pixel_std = load_model_and_assets(
            self.model_dir, self.save_format
        )

        # モデルをGPUに移動
        self.model = self.model.to(self.device)
        self.pixel_std_safe = np.where(self.pixel_std == 0, 1e-6, self.pixel_std)

        self.image_store = OrderedDict()

        self._warmup()

        self.logger.info(f"PatchCoreInferenceEngine started - id={id(self)}, model={self.model_name}")
        self.logger.info(f"Device={self.device}, Mixed Precision={self.use_mixed_precision}")

    def _reload_settings(self) -> None:
        """
        設定ファイルを再読み込み

        settings.pyの変更を反映させるために使用します。
        """
        self.loader.reload()
        self.affine_points = self.loader.get_variable("AFFINE_POINTS")
        self.image_size = self.loader.get_variable("IMAGE_SIZE")
        self.save_format = self.loader.get_variable("SAVE_FORMAT")
        self.z_score_threshold = self.loader.get_variable("Z_SCORE_THRESHOLD")
        self.z_area_threshold = self.loader.get_variable("Z_AREA_THRESHOLD")
        self.z_max_threshold = self.loader.get_variable("Z_MAX_THRESHOLD")
        self.ng_image_save = self.loader.get_variable("NG_IMAGE_SAVE")
        self.max_images = self.loader.get_variable("MAX_CACHE_IMAGE")

        # GPU設定の再読み込み
        self.use_gpu = self.loader.get_variable("USE_GPU")
        self.device_id = self.loader.get_variable("GPU_DEVICE_ID")
        self.use_mixed_precision = self.loader.get_variable("USE_MIXED_PRECISION")

        self.logger.info(f"Settings reloaded for model={self.model_name}")

    def _warmup(self) -> None:
        """
        ウォームアップ推論を実行

        ダミー画像で推論を行い、モデルとGPUを初期化します。
        これにより最初の実際の推論が高速化されます。
        """
        try:
            dummy = np.zeros((self.image_size[1], self.image_size[0], 3), dtype=np.uint8)
            inputs = preprocess_cv2(dummy, self.affine_points, self.image_size)
            inputs = inputs.to(self.device)
            _ = self._run_model(inputs)
            self.logger.info("Warmup complete")
        except Exception as e:
            self.logger.error(f"Warmup failed: {e}", exc_info=True)

    def get_model_name(self) -> str:
        """
        モデル名を取得

        Returns:
            モデル名の文字列
        """
        return str(self.model_name)

    def __del__(self):
        """デストラクタ：GPUキャッシュをクリア"""
        clear_gpu_cache()
        self.logger.info(f"PatchCoreInferenceEngine ended - id={id(self)}, model={self.model_name}")

    def _log_result(self, result: dict) -> None:
        """
        推論結果をログファイルに記録

        日付別のログファイルとNG専用ログファイルに記録します。

        Args:
            result: 推論結果の辞書（label, z_stats, thresholds, image_id を含む）
        """
        date_str = datetime.now().strftime("%Y%m%d")
        log_filename = f"inference_{date_str}.log"
        log_path = os.path.join(self.settings_dir, "execute", "log")
        os.makedirs(log_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(log_path, log_filename), "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}]: {result}\n")
        if result["label"] == "NG":
            with open(os.path.join(log_path, "NG.log"), "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}]: {result}\n")

    def _store_image(self, image_id: str, image: np.ndarray) -> None:
        """
        画像をメモリキャッシュに保存

        キャッシュサイズが上限を超える場合は、最古の画像を削除します（FIFO）。

        Args:
            image_id: 画像を識別するユニークなID
            image: 保存する画像配列
        """
        self.image_store[image_id] = image
        if len(self.image_store) > self.max_images:
            self.image_store.popitem(last=False)  # 最古の画像を削除

    def get_image_by_id(self, image_id: str) -> Optional[np.ndarray]:
        """
        IDから画像を取得

        Args:
            image_id: 取得する画像のID

        Returns:
            画像配列。存在しない場合はNone
        """
        return self.image_store.get(image_id)

    def get_store_image_list(self) -> list:
        """
        キャッシュされている画像IDのリストを取得

        Returns:
            画像IDのリスト（新しい順）
        """
        return list(reversed(self.image_store.keys()))

    def clear_store_image(self) -> None:
        """
        画像キャッシュをクリア

        すべての保存済み画像をメモリから削除します。
        """
        self.image_store = OrderedDict()

    def _run_model(self, inputs: torch.Tensor) -> np.ndarray:
        """
        モデルを実行して異常スコアマップを生成

        特徴マップを抽出し、PCA変換後にメモリバンクとの距離を計算します。

        Args:
            inputs: 前処理済みの入力テンソル（形状: [1, C, H, W]）

        Returns:
            異常スコアマップ（2D NumPy配列）
        """
        inputs = inputs.to(self.device)

        with torch.no_grad():
            # 新しいautocast APIを使用
            if self.use_mixed_precision and self.device.type == "cuda":
                with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                    fmap = self.model(inputs)
            else:
                fmap = self.model(inputs)

            patches = fmap.squeeze(0).permute(1, 2, 0).reshape(-1, fmap.size(1))
            patches = patches.cpu().numpy()  # CPUに戻す
            patches = self.pca.transform(patches)
            scores = np.linalg.norm(patches - self.memory_bank.mean(axis=0), axis=1)
            return scores.reshape(fmap.shape[2], fmap.shape[3])

    def _resize_score_map(self, score_map: np.ndarray) -> np.ndarray:
        """
        スコアマップを元画像サイズにリサイズ

        Args:
            score_map: 異常スコアマップ

        Returns:
            リサイズされたスコアマップ
        """
        return cv2.resize(score_map, self.image_size, interpolation=cv2.INTER_CUBIC)

    def _compute_z_score_map(self, raw_score_map: np.ndarray) -> np.ndarray:
        """
        Z-scoreマップを計算

        正常画像の統計情報を使用してスコアを標準化します。

        Args:
            raw_score_map: 元の異常スコアマップ

        Returns:
            Z-scoreマップ
        """
        return (raw_score_map - self.pixel_mean) / self.pixel_std_safe

    def _generate_overlay(self, inputs: torch.Tensor, z_score_map: np.ndarray) -> np.ndarray:
        """
        ヒートマップ重畳画像を生成

        Z-scoreマップをJETカラーマップで可視化し、元画像に重ねます。

        Args:
            inputs: 入力画像テンソル
            z_score_map: Z-scoreマップ

        Returns:
            ヒートマップが重畳された画像（BGR形式）
        """
        z_vis = np.clip(z_score_map, 0, 5.0)
        z_vis = (z_vis / 5.0 * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(z_vis, cv2.COLORMAP_JET)
        input_img = (inputs.squeeze(0).permute(1, 2, 0).numpy() * 255).astype(np.uint8)
        return cv2.addWeighted(cv2.cvtColor(input_img, cv2.COLOR_RGB2BGR), 0.6, heatmap, 0.4, 0)

    def _result_gen(self, label: LabelType, z_stats: dict, image_id: str) -> PredictionResult:
        """
        推論結果を整形

        Args:
            label: 判定結果（"OK" または "NG"）
            z_stats: Z-score統計情報の辞書
            image_id: 画像ID

        Returns:
            整形された推論結果
        """
        return {
            "label": label,
            "z_stats": {k: float(v) for k, v in z_stats.items()},
            "thresholds": {
                "z_score": self.z_score_threshold,
                "z_area": self.z_area_threshold,
                "z_max": self.z_max_threshold,
            },
            "image_id": {
                "original": f"org_{image_id}",
                "overlay": f"ovr_{image_id}",
            },
        }

    def predict(self, image_array: np.ndarray) -> PredictionResult:
        """
        画像の異常検出推論を実行

        入力画像を前処理し、モデルで推論を行い、結果を整形して返します。
        NG画像は自動的に保存されます（設定により）。

        Args:
            image_array: 入力画像（BGR形式のNumPy配列）

        Returns:
            推論結果（label, z_stats, thresholds, image_id を含む）

        Example:
            >>> engine = PatchCoreInferenceEngine("example_model")
            >>> img = cv2.imread("test.jpg")
            >>> result = engine.predict(img)
            >>> print(result["label"])  # "OK" or "NG"
        """
        # 入力画像のテンソル化
        inputs = preprocess_cv2(image_array, self.affine_points, self.image_size)

        # 特徴マップからスコアマップ生成
        score_map = self._run_model(inputs)

        # スコアマップを元画像サイズにリサイズ
        raw_score_map = self._resize_score_map(score_map)

        # Zスコアマップ生成
        z_score_map = self._compute_z_score_map(raw_score_map)

        # Zスコア統計と判定
        z_stats = evaluate_z_score_map(z_score_map, self.z_score_threshold)
        is_ok = is_ok_z(z_stats, self.z_area_threshold, self.z_max_threshold)

        # 可視化オーバーレイ生成
        overlay = self._generate_overlay(inputs, z_score_map)

        # 画像ID生成とキャッシュ保存
        label_str = "OK" if is_ok else "NG"
        image_id = f"{label_str}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}"
        self._store_image(f"org_{image_id}", image_array)
        self._store_image(f"ovr_{image_id}", overlay)

        # NG画像保存（非同期）
        if not is_ok and self.ng_image_save:
            save_dir = os.path.join(
                self.settings_dir, "execute", "NG", datetime.now().strftime("%Y%m%d"), datetime.now().strftime("%H%M")
            )
            os.makedirs(save_dir, exist_ok=True)
            self._save_ng_images_async(save_dir, image_id, overlay, image_array)

        # 結果整形とログ
        result = self._result_gen(label_str, z_stats, image_id)
        self._log_result(result)

        return result

    def _save_ng_images_async(self, save_dir: str, image_id: str, overlay: np.ndarray, original: np.ndarray) -> None:
        """
        NG画像を非同期で保存

        別スレッドで画像を保存するため、メイン処理をブロックしません。

        Args:
            save_dir: 保存先ディレクトリのパス
            image_id: 画像ID（ファイル名に使用）
            overlay: ヒートマップ重畳画像
            original: オリジナル画像
        """

        def save():
            try:
                cv2.imwrite(os.path.join(save_dir, f"{image_id}_overlay.png"), overlay)
                cv2.imwrite(os.path.join(save_dir, f"{image_id}_original.png"), original)
            except Exception as e:
                self.logger.error(f"NG image save failed: {e}")

        threading.Thread(target=save, daemon=True).start()
