"""
設定ファイル検証スクリプト
モデル設定の妥当性をチェック
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.settings_loader import SettingsLoader
import argparse


def validate_settings(settings_path: str) -> bool:
    """
    設定ファイルを検証

    Args:
        settings_path (str): 設定ファイルパス

    Returns:
        bool: 検証成功
    """
    print(f"設定ファイルを検証中: {settings_path}")
    print("=" * 60)

    try:
        loader = SettingsLoader(settings_path)
        print("✓ 設定ファイルの読み込み成功")

        # 基本設定の表示
        print("\n基本設定:")
        print(f"  IMAGE_SIZE: {loader.get_variable('IMAGE_SIZE')}")
        print(f"  FEATURE_DEPTH: {loader.get_variable('FEATURE_DEPTH')}")
        print(f"  SAVE_FORMAT: {loader.get_variable('SAVE_FORMAT')}")
        print(f"  USE_GPU: {loader.get_variable('USE_GPU')}")

        # しきい値の表示
        print("\nしきい値設定:")
        print(f"  Z_SCORE_THRESHOLD: {loader.get_variable('Z_SCORE_THRESHOLD')}")
        print(f"  Z_AREA_THRESHOLD: {loader.get_variable('Z_AREA_THRESHOLD')}")
        print(f"  Z_MAX_THRESHOLD: {loader.get_variable('Z_MAX_THRESHOLD')}")

        # 詳細検証
        is_valid, errors = loader.validate_model_settings()

        if is_valid:
            print("\n" + "=" * 60)
            print("✓ 設定ファイルは正常です")
            return True
        else:
            print("\n" + "=" * 60)
            print("✗ 設定ファイルにエラーがあります:")
            for error in errors:
                print(f"  - {error}")
            return False

    except FileNotFoundError as e:
        print(f"✗ エラー: {e}")
        return False
    except Exception as e:
        print(f"✗ 予期しないエラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="設定ファイル検証ツール")
    parser.add_argument(
        "settings_path",
        nargs="?",
        default="settings/models/example_model/settings.py",
        help="検証する設定ファイルのパス",
    )

    args = parser.parse_args()

    success = validate_settings(args.settings_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
