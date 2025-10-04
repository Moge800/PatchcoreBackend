"""簡易テスト"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.settings_loader import SettingsLoader

# 設定読み込み
loader = SettingsLoader("settings/models/example_model/settings.py")

# 検証実行
valid, errors = loader.validate_model_settings()

# 結果表示
if valid:
    print("✓ 検証成功: SettingsLoaderの検証メソッドが正常に動作しています")
else:
    print("✗ 検証失敗:")
    for error in errors:
        print(f"  - {error}")
