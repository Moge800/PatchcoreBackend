"""
ロギング設定モジュール
プロジェクト全体で統一されたロギングを提供
"""

import logging
import os
from datetime import datetime
from src.config import env_loader


def setup_logger(
    name: str, log_dir: str = None, level: int = None, console: bool = True, file: bool = True
) -> logging.Logger:
    """
    標準化されたロガーを作成
    環境変数からデフォルト値を読み込む

    Args:
        name (str): ロガー名
        log_dir (str): ログディレクトリ（省略時は環境変数から取得）
        level (int): ログレベル（省略時は環境変数から取得）
        console (bool): コンソール出力を有効化
        file (bool): ファイル出力を有効化

    Returns:
        logging.Logger: 設定済みロガー
    """
    # 環境変数からデフォルト値を取得
    if log_dir is None:
        log_dir = env_loader.LOG_DIR
    if level is None:
        level_str = env_loader.LOG_LEVEL
        level = getattr(logging, level_str.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 既存のハンドラをクリア
    if logger.handlers:
        logger.handlers.clear()

    # フォーマッター
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # コンソールハンドラ
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # ファイルハンドラ
    if file:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    既存のロガーを取得、なければ作成

    Args:
        name (str): ロガー名

    Returns:
        logging.Logger: ロガーインスタンス
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
