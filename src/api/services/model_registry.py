"""
モデルレジストリサービス

複数の PatchCore 推論エンジンをメモリ上で管理します。
モデルのロード・アンロード・削除を API 経由で操作できます。
"""

import asyncio
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from src.config import env_loader
from src.ml_engines.PatchCore.core.inference_engine import PatchCoreInferenceEngine
from src.utils.logger import setup_logger

logger = setup_logger("model_registry", log_dir=env_loader.LOG_DIR + "/api")


@dataclass
class ModelEntry:
    name: str
    engine: Optional[PatchCoreInferenceEngine]
    status: str  # "loaded" | "unloaded"
    loaded_at: Optional[datetime] = field(default=None)
    error: Optional[str] = field(default=None)


class ModelRegistry:
    """
    複数の PatchCoreInferenceEngine インスタンスを管理するレジストリ。

    モデルのロード・アンロード・削除を行い、ジョブキューからのエンジン取得を
    同期ファストパスで提供します。
    """

    def __init__(self) -> None:
        self._registry: Dict[str, ModelEntry] = {}
        self._lock = asyncio.Lock()

    def _available_model_names(self) -> List[str]:
        """settings/models/ 以下のモデル名を一覧取得"""
        settings_base = env_loader.SETTINGS_DIR
        models_dir = os.path.join(settings_base, "models")
        if not os.path.isdir(models_dir):
            return []
        return [
            d for d in os.listdir(models_dir)
            if os.path.isdir(os.path.join(models_dir, d))
        ]

    def list_models(self) -> List[ModelEntry]:
        """
        既知の全モデルを返す（ディスク上 + メモリ上のマージ）。

        ディスク上のモデルでレジストリに未登録のものは "unloaded" として返します。
        """
        result: Dict[str, ModelEntry] = {}

        # ディスク上のモデルをベースにする
        for name in self._available_model_names():
            if name in self._registry:
                result[name] = self._registry[name]
            else:
                result[name] = ModelEntry(name=name, engine=None, status="unloaded")

        # レジストリにあってディスクに見つからない場合も含める（削除途中など）
        for name, entry in self._registry.items():
            if name not in result:
                result[name] = entry

        return list(result.values())

    def get_engine(self, model_name: str) -> PatchCoreInferenceEngine:
        """
        ロード済みエンジンを同期で取得する。ジョブワーカーから呼ぶ用。

        Raises:
            KeyError: モデルが未登録（存在しない）
            RuntimeError: モデルが登録済みだがアンロード済み
        """
        if model_name not in self._registry:
            raise KeyError(f"Model '{model_name}' not found")
        entry = self._registry[model_name]
        if entry.engine is None or entry.status != "loaded":
            raise RuntimeError(f"Model '{model_name}' is not loaded")
        return entry.engine

    async def load(self, model_name: str) -> ModelEntry:
        """
        モデルをメモリにロードする。

        コンストラクタはブロッキング処理（torch.load 等）を含むため
        スレッドプールで実行します。

        Raises:
            ValueError: 既にロード済み
            FileNotFoundError: モデルファイルが見つからない
        """
        async with self._lock:
            if model_name in self._registry and self._registry[model_name].status == "loaded":
                raise ValueError(f"Model '{model_name}' is already loaded")

            logger.info(f"Loading model: {model_name}")
            loop = asyncio.get_event_loop()
            try:
                engine: PatchCoreInferenceEngine = await loop.run_in_executor(
                    None, PatchCoreInferenceEngine, model_name
                )
            except FileNotFoundError as e:
                logger.error(f"Model files not found for '{model_name}': {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to load model '{model_name}': {e}", exc_info=True)
                self._registry[model_name] = ModelEntry(
                    name=model_name, engine=None, status="unloaded", error=str(e)
                )
                raise

            entry = ModelEntry(
                name=model_name,
                engine=engine,
                status="loaded",
                loaded_at=datetime.now(),
            )
            self._registry[model_name] = entry
            logger.info(f"Model loaded: {model_name}")
            return entry

    async def unload(self, model_name: str) -> None:
        """
        モデルをメモリからアンロードする（ファイルは残す）。

        Raises:
            KeyError: モデルが未登録
            ValueError: 既にアンロード済み
        """
        async with self._lock:
            if model_name not in self._registry:
                raise KeyError(f"Model '{model_name}' not found in registry")
            entry = self._registry[model_name]
            if entry.status != "loaded":
                raise ValueError(f"Model '{model_name}' is not loaded")

            entry.engine = None
            entry.status = "unloaded"
            entry.loaded_at = None
            logger.info(f"Model unloaded: {model_name}")

    async def delete(self, model_name: str) -> None:
        """
        モデルをアンロードし、ディスク上のファイルも削除する。

        削除対象:
        - models/{model_name}/
        - settings/models/{model_name}/

        Raises:
            KeyError: モデルが未登録かつディスク上にも存在しない
        """
        # ロード済みなら先にアンロード
        if model_name in self._registry and self._registry[model_name].status == "loaded":
            await self.unload(model_name)

        model_dir = os.path.join(env_loader.MODEL_DIR, model_name)
        settings_dir = os.path.join(env_loader.SETTINGS_DIR, "models", model_name)
        deleted_any = False

        if os.path.isdir(model_dir):
            shutil.rmtree(model_dir)
            logger.info(f"Deleted model directory: {model_dir}")
            deleted_any = True

        if os.path.isdir(settings_dir):
            shutil.rmtree(settings_dir)
            logger.info(f"Deleted settings directory: {settings_dir}")
            deleted_any = True

        if not deleted_any and model_name not in self._registry:
            raise KeyError(f"Model '{model_name}' not found")

        self._registry.pop(model_name, None)
        logger.info(f"Model deleted: {model_name}")

    async def load_startup_models(self, names: List[str]) -> None:
        """起動時に指定モデルを順番にロードする"""
        for name in names:
            try:
                await self.load(name)
            except Exception as e:
                logger.error(f"Startup load failed for '{name}': {e}")
