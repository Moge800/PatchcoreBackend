"""
ロギング設定モジュール

プロジェクト全体で統一されたロギングを提供します。
環境変数から設定を読み込み、コンソールとファイル出力を管理します。
"""

import logging
import os
from datetime import datetime
from typing import Optional
from src.config import env_loader


def setup_logger(
    name: str,
    log_dir: Optional[str] = None,
    level: Optional[int] = None,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    標準化されたロガーを作成

    環境変数からデフォルト値を読み込み、コンソールとファイル出力を設定します。
    既存のハンドラは自動的にクリアされます。

    Args:
        name: ロガー名（通常はモジュール名 __name__ を使用）
        log_dir: ログディレクトリのパス。Noneの場合は環境変数LOG_DIRから取得
        level: ログレベル（logging.DEBUG, INFO, WARNING, ERROR, CRITICAL）
               Noneの場合は環境変数LOG_LEVELから取得
        console: Trueの場合、標準出力にログを出力
        file: Trueの場合、ファイルにログを出力（ファイル名: {name}_YYYYMMDD.log）

    Returns:
        設定済みのロガーインスタンス

    Example:
        >>> logger = setup_logger(__name__, level=logging.DEBUG)
        >>> logger.info("アプリケーション起動")
    """
    # 環境変数からデフォルト値を取得
    if log_dir is None:
        log_dir = env_loader.LOG_DIR
    if level is None:
        level_str = env_loader.LOG_LEVEL
        level = getattr(logging, level_str.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 既存のハンドラをクリア（重複出力を防止）
    if logger.handlers:
        logger.handlers.clear()

    # フォーマッター（タイムスタンプ - ロガー名 - レベル - メッセージ）
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
    既存のロガーを取得、存在しない場合は新規作成

    指定された名前のロガーが既に存在し、ハンドラが設定されている場合はそれを返します。
    存在しない、またはハンドラが未設定の場合は setup_logger() を呼び出して新規作成します。

    Args:
        name: ロガー名（通常はモジュール名 __name__ を使用）

    Returns:
        ロガーインスタンス（既存または新規作成）

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.warning("注意が必要です")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
