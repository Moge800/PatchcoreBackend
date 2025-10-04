"""
設定ファイルローダーモジュール

モデル固有のsettings.pyファイルを動的に読み込み、環境変数でオーバーライド可能にします。
"""

import os
import importlib.util
from typing import Any, Tuple, List, Dict, Optional
from src.config import env_loader


class SettingsLoader:
    """
    モデル固有のsettings.pyを動的に読み込むクラス

    環境変数による設定のオーバーライドをサポートします。
    """

    def __init__(self, settings_path: str) -> None:
        """
        SettingsLoaderを初期化し、settings.pyを読み込む

        Args:
            settings_path: settings.pyファイルへのフルパス

        Raises:
            FileNotFoundError: settings.pyが存在しない場合
            RuntimeError: settings.pyの読み込みに失敗した場合
        """
        self.settings_path = settings_path
        if not os.path.isfile(settings_path):
            raise FileNotFoundError(f"{settings_path} が存在しません。settings.py を配置してください。")

        try:
            self.reload()
        except Exception as e:
            raise RuntimeError(f"settings.py の読み込みに失敗しました: {e}")

    def get_variable(self, name: str) -> Any:
        """
        settings.pyから変数を取得（環境変数でオーバーライド可能）

        環境変数が設定されている場合は、settings.pyの値を上書きします。

        Args:
            name: 取得する変数名

        Returns:
            変数の値（環境変数でオーバーライドされる場合はその値）

        Raises:
            AttributeError: 変数がsettings.pyに定義されていない場合

        Example:
            >>> loader = SettingsLoader("models/example_model/settings.py")
            >>> image_size = loader.get_variable("IMAGE_SIZE")
            >>> print(image_size)
            (256, 256)
        """
        # 環境変数からのオーバーライドマッピング
        # settings.pyで定義されている設定のうち、環境変数で上書き可能なもの
        env_override_map: Dict[str, Tuple[Optional[str], Optional[type]]] = {
            "USE_GPU": ("USE_GPU", bool),
            "GPU_DEVICE_ID": ("GPU_DEVICE_ID", int),
            "USE_MIXED_PRECISION": ("USE_MIXED_PRECISION", bool),
            "CPU_OPTIMIZATION": (None, None),  # 特殊処理
            "MAX_CACHE_IMAGE": ("MAX_CACHE_IMAGES", int),
            "NG_IMAGE_SAVE": ("NG_IMAGE_SAVE", bool),
        }

        # 環境変数でのオーバーライドを試みる
        if name in env_override_map:
            env_key, cast_type = env_override_map[name]

            # CPU_OPTIMIZATIONの特殊処理
            if name == "CPU_OPTIMIZATION":
                return env_loader.get_cpu_optimization()

            # 環境変数が設定されているか確認
            env_value = getattr(env_loader, env_key, None)
            if env_value is not None:
                # .envファイルが実際に存在し、値が設定されている場合のみオーバーライド
                if hasattr(env_loader, "_env_path") and env_loader._env_path.exists():
                    return env_value

        # settings.pyから値を取得
        if not hasattr(self.module, name):
            raise AttributeError(f"{name} が {self.module.__name__} に定義されていません。")
        return getattr(self.module, name)

    def reload(self) -> None:
        """
        設定ファイルを再読み込み

        settings.pyの内容が変更された場合に、変更を反映させるために使用します。
        """
        spec = importlib.util.spec_from_file_location("settings", self.settings_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def validate_model_settings(self) -> Tuple[bool, List[str]]:
        """
        モデル設定の妥当性を検証

        settings.pyの必須項目と値の範囲をチェックします。
        環境変数でオーバーライドされる設定は検証対象外です。

        Returns:
            検証結果のタプル
            - bool: 検証が成功した場合True、失敗した場合False
            - List[str]: エラーメッセージのリスト（検証成功時は空）

        Example:
            >>> loader = SettingsLoader("models/example_model/settings.py")
            >>> is_valid, errors = loader.validate_model_settings()
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"検証エラー: {error}")
        """
        errors: List[str] = []

        # 必須設定の確認（settings.py固有の設定のみ）
        required_vars = [
            "AFFINE_POINTS",  # GUIで設定
            "IMAGE_SIZE",  # モデル設計
            "Z_SCORE_THRESHOLD",  # 異常検出コア設定
            "Z_AREA_THRESHOLD",  # 異常検出コア設定
            "Z_MAX_THRESHOLD",  # 異常検出コア設定
            "PCA_VARIANCE",  # 異常検出に関与
            "FEATURE_DEPTH",  # モデル設計
            "SAVE_FORMAT",  # モデル保存形式
            "ENABLE_AUGMENT",  # 学習コア設定
        ]

        for var in required_vars:
            try:
                self.get_variable(var)
            except AttributeError:
                errors.append(f"必須設定 '{var}' が定義されていません")

        # 設定値の検証
        try:
            # AFFINE_POINTS検証
            affine_points = self.get_variable("AFFINE_POINTS")
            if not isinstance(affine_points, list) or len(affine_points) != 4:
                errors.append("AFFINE_POINTS は4点のリストである必要があります")
            else:
                # 各点が[x, y]形式か確認
                for i, point in enumerate(affine_points):
                    if not isinstance(point, (list, tuple)) or len(point) != 2:
                        errors.append(f"AFFINE_POINTS[{i}] は [x, y] 形式である必要があります")

            # IMAGE_SIZE検証
            image_size = self.get_variable("IMAGE_SIZE")
            if not isinstance(image_size, (tuple, list)) or len(image_size) != 2:
                errors.append("IMAGE_SIZE は (width, height) のタプルである必要があります")
            else:
                if not all(isinstance(x, int) and x > 0 for x in image_size):
                    errors.append("IMAGE_SIZE の値は正の整数である必要があります")

            # しきい値チェック
            for threshold_name in ["Z_SCORE_THRESHOLD", "Z_MAX_THRESHOLD"]:
                threshold = self.get_variable(threshold_name)
                if not isinstance(threshold, (int, float)) or threshold <= 0:
                    errors.append(f"{threshold_name} は正の数値である必要があります")

            # Z_AREA_THRESHOLDは0以上のピクセル数
            z_area = self.get_variable("Z_AREA_THRESHOLD")
            if not isinstance(z_area, (int, float)) or z_area < 0:
                errors.append("Z_AREA_THRESHOLD は0以上の数値である必要があります")

            # PCA設定チェック（異常検出に関与）
            pca_variance = self.get_variable("PCA_VARIANCE")
            if not isinstance(pca_variance, (int, float)) or not (0 < pca_variance <= 1):
                errors.append("PCA_VARIANCE は 0 < x <= 1 の範囲である必要があります")

            # 特徴深度チェック
            feature_depth = self.get_variable("FEATURE_DEPTH")
            if not isinstance(feature_depth, int) or feature_depth not in [1, 2, 3, 4]:
                errors.append("FEATURE_DEPTH は 1, 2, 3, 4 のいずれかである必要があります")

            # 保存形式チェック
            save_format = self.get_variable("SAVE_FORMAT")
            if save_format not in ["compressed", "full"]:
                errors.append("SAVE_FORMAT は 'compressed' または 'full' である必要があります")

            # データ拡張設定チェック
            enable_augment = self.get_variable("ENABLE_AUGMENT")
            if not isinstance(enable_augment, bool):
                errors.append("ENABLE_AUGMENT は True または False である必要があります")

        except AttributeError as e:
            errors.append(str(e))

        return len(errors) == 0, errors
