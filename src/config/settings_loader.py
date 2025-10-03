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
        spec = importlib.util.spec_from_file_location("settings", self.settings_path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
