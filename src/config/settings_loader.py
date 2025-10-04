import os
import importlib.util


class SettingsLoader:
    def __init__(self, settings_path: str):
        """
        Initialize the loader with the path to settings.py

        Args:
            settings_path (str): Full path to settings.py
        """
        self.settings_path = settings_path
        if not os.path.isfile(settings_path):
            raise FileNotFoundError(f"{settings_path} が存在しません。settings.py を配置してください。")

        try:
            self.reload()
        except Exception as e:
            raise RuntimeError(f"settings.py の読み込みに失敗しました: {e}")

    def get_variable(self, name: str):
        """
        Retrieve a variable from the loaded settings module.

        Args:
            name (str): Variable name to retrieve

        Returns:
            Any: Value of the variable

        Raises:
            AttributeError: If the variable is not defined in settings.py
        """
        if not hasattr(self.module, name):
            raise AttributeError(f"{name} が {self.module.__name__} に定義されていません。")
        return getattr(self.module, name)

    def reload(self):
        """設定ファイルを再読み込み"""
        spec = importlib.util.spec_from_file_location("settings", self.settings_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def validate_model_settings(self) -> tuple[bool, list[str]]:
        """
        モデル設定の妥当性を検証

        Returns:
            tuple[bool, list[str]]: (検証成功, エラーメッセージリスト)
        """
        errors = []

        # 必須設定の確認
        required_vars = [
            "AFFINE_POINTS",
            "IMAGE_SIZE",
            "Z_SCORE_THRESHOLD",
            "Z_AREA_THRESHOLD",
            "Z_MAX_THRESHOLD",
            "PCA_VARIANCE",
            "FEATURE_DEPTH",
            "SAVE_FORMAT",
            "USE_GPU",
        ]

        for var in required_vars:
            try:
                self.get_variable(var)
            except AttributeError:
                errors.append(f"必須設定 '{var}' が定義されていません")

        # 設定値の検証
        try:
            affine_points = self.get_variable("AFFINE_POINTS")
            if not isinstance(affine_points, list) or len(affine_points) != 4:
                errors.append("AFFINE_POINTS は4点のリストである必要があります")

            image_size = self.get_variable("IMAGE_SIZE")
            if not isinstance(image_size, (tuple, list)) or len(image_size) != 2:
                errors.append("IMAGE_SIZE は (width, height) のタプルである必要があります")

            # しきい値チェック
            for threshold_name in ["Z_SCORE_THRESHOLD", "Z_MAX_THRESHOLD"]:
                threshold = self.get_variable(threshold_name)
                if not isinstance(threshold, (int, float)) or threshold <= 0:
                    errors.append(f"{threshold_name} は正の数値である必要があります")

            # Z_AREA_THRESHOLDは整数でピクセル数
            z_area = self.get_variable("Z_AREA_THRESHOLD")
            if not isinstance(z_area, (int, float)) or z_area < 0:
                errors.append("Z_AREA_THRESHOLD は0以上の数値である必要があります")

            # PCA設定チェック
            pca_variance = self.get_variable("PCA_VARIANCE")
            if not (0 < pca_variance <= 1):
                errors.append("PCA_VARIANCE は 0 < x <= 1 の範囲である必要があります")

            # 特徴深度チェック
            feature_depth = self.get_variable("FEATURE_DEPTH")
            if feature_depth not in [1, 2, 3, 4]:
                errors.append("FEATURE_DEPTH は 1, 2, 3, 4 のいずれかである必要があります")

            # 保存形式チェック
            save_format = self.get_variable("SAVE_FORMAT")
            if save_format not in ["compressed", "full"]:
                errors.append("SAVE_FORMAT は 'compressed' または 'full' である必要があります")

        except AttributeError as e:
            errors.append(str(e))

        return len(errors) == 0, errors
