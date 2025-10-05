import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
from datetime import datetime

# パスを追加してsrcモジュールをインポート可能にする
sys.path.insert(0, os.path.abspath("."))
from src.config.settings_loader import SettingsLoader

ENV_FILE_PATH = ".env"


def read_model_name_from_env():
    """環境変数ファイル(.env)からDEFAULT_MODEL_NAMEを読み込む"""
    try:
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("DEFAULT_MODEL_NAME"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Error reading DEFAULT_MODEL_NAME from .env: {e}")
    return None


def write_model_name_to_env(new_model_name):
    """環境変数ファイル(.env)のDEFAULT_MODEL_NAMEを更新"""
    try:
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
            found = False
            for line in lines:
                if line.strip().startswith("DEFAULT_MODEL_NAME"):
                    f.write(f"DEFAULT_MODEL_NAME={new_model_name}\n")
                    found = True
                else:
                    f.write(line)

            # DEFAULT_MODEL_NAMEが存在しない場合は追加
            if not found:
                f.write(f"\n# モデル設定\nDEFAULT_MODEL_NAME={new_model_name}\n")

    except Exception as e:
        print(f"Error writing DEFAULT_MODEL_NAME to .env: {e}")
        raise


class ModelLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PatchCoreモデル操作GUI")
        self.root.geometry("800x700")  # 初期サイズを設定
        self.root.minsize(700, 600)  # 最小サイズを設定
        self.root.resizable(True, True)  # リサイズ可能にする
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.model_base_dir = os.path.join("settings", "models")
        self.model_dirs = [
            d for d in os.listdir(self.model_base_dir) if os.path.isdir(os.path.join(self.model_base_dir, d))
        ]
        self.has_models = len(self.model_dirs) > 0
        self.selected_model = tk.StringVar(value=self.model_dirs[0] if self.has_models else "")
        self.current_model_name = read_model_name_from_env()  # .envから読み込み

        self._setup_widgets()
        self._update_button_states()

    def _setup_widgets(self):
        # ヘッダー部分
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        self.model_label = tk.Label(
            header_frame, text=f"現在モデル名: {self.selected_model.get()}", font=("Arial", 14, "bold")
        )
        self.model_label.pack(pady=(0, 10))

        dropdown_frame = ttk.Frame(header_frame)
        dropdown_frame.pack(pady=5)

        tk.Label(dropdown_frame, text="モデル選択:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))

        self.model_dropdown = ttk.Combobox(
            dropdown_frame, textvariable=self.selected_model, values=self.model_dirs, state="readonly", width=25
        )
        self.model_dropdown.pack(side=tk.LEFT)
        self.model_dropdown.bind("<<ComboboxSelected>>", self._on_model_select)

        self.confirm_button = tk.Button(
            dropdown_frame,
            text="確定",
            command=self._on_confirm_model,
            font=("Arial", 10),
            bg="#d4edda",
            relief=tk.RAISED,
        )
        self.confirm_button.pack(side=tk.LEFT, padx=(10, 0))

        # ログエリア
        log_frame = ttk.LabelFrame(self.root, text="ログ", padding=(5, 5))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=12, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # ボタンエリアのメインフレーム
        button_main_frame = ttk.Frame(self.root)
        button_main_frame.pack(fill=tk.X, padx=10, pady=10)

        # 設定関連ボタンパネル
        settings_frame = ttk.LabelFrame(button_main_frame, text="設定編集", padding=(10, 5))
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 設定ボタンを2列レイアウト
        settings_left_frame = ttk.Frame(settings_frame)
        settings_left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        settings_right_frame = ttk.Frame(settings_frame)
        settings_right_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self.edit_button = tk.Button(
            settings_left_frame,
            text="⚙️ 設定編集 (GUI)",
            font=("Arial", 11),
            width=20,
            command=self._on_edit_settings_click,
            bg="#e8f5e8",
            relief=tk.RAISED,
        )
        self.edit_button.pack(pady=2, padx=5, fill=tk.X)

        self.edit_file_button = tk.Button(
            settings_left_frame,
            text="📝 設定編集 (ファイル)",
            font=("Arial", 11),
            width=20,
            command=self._on_edit_settings_file_click,
            relief=tk.RAISED,
        )
        self.edit_file_button.pack(pady=2, padx=5, fill=tk.X)

        self.validate_button = tk.Button(
            settings_left_frame,
            text="✅ 設定検証",
            font=("Arial", 11),
            width=20,
            command=self._on_validate_settings_click,
            bg="#e3f2fd",
            relief=tk.RAISED,
        )
        self.validate_button.pack(pady=2, padx=5, fill=tk.X)

        self.env_button = tk.Button(
            settings_right_frame,
            text="🌐 .env編集 (GUI)",
            font=("Arial", 11),
            width=20,
            command=self._on_edit_env_click,
            bg="#fff3e0",
            relief=tk.RAISED,
        )
        self.env_button.pack(pady=2, padx=5, fill=tk.X)

        self.env_file_button = tk.Button(
            settings_right_frame,
            text="📄 .env編集 (ファイル)",
            font=("Arial", 11),
            width=20,
            command=self._on_edit_env_file_click,
            bg="#fff8e1",
            relief=tk.RAISED,
        )
        self.env_file_button.pack(pady=2, padx=5, fill=tk.X)

        self.affine_button = tk.Button(
            settings_right_frame,
            text="📐 アフィン座標取得",
            font=("Arial", 11),
            width=20,
            command=self._on_affine_point_click,
            relief=tk.RAISED,
        )
        self.affine_button.pack(pady=2, padx=5, fill=tk.X)

        # 実行関連ボタンパネル
        execution_frame = ttk.LabelFrame(button_main_frame, text="学習・推論実行", padding=(10, 5))
        execution_frame.pack(fill=tk.X, pady=(0, 5))

        # 実行ボタンを横並びレイアウト
        execution_button_frame = ttk.Frame(execution_frame)
        execution_button_frame.pack()

        self.train_button = tk.Button(
            execution_button_frame,
            text="🎯 学習実行",
            font=("Arial", 12, "bold"),
            width=15,
            command=self._on_train_button_click,
            bg="#ffebee",
            fg="#c62828",
            relief=tk.RAISED,
        )
        self.train_button.pack(side=tk.LEFT, pady=5, padx=10)

        self.inference_button = tk.Button(
            execution_button_frame,
            text="🔍 テスト推論実行",
            font=("Arial", 12, "bold"),
            width=15,
            command=self._on_inference_button_click,
            bg="#e8f5e0",
            fg="#2e7d32",
            relief=tk.RAISED,
        )
        self.inference_button.pack(side=tk.LEFT, pady=5, padx=10)

        self.control_widgets = [
            self.edit_button,
            self.edit_file_button,
            self.validate_button,
            self.env_button,
            self.env_file_button,
            self.affine_button,
            self.train_button,
            self.inference_button,
            self.confirm_button,
        ]

    def _on_model_select(self, event):
        self.model_label.config(text=f"現在モデル名: {self.selected_model.get()}")
        self._update_button_states()

    def _on_confirm_model(self):
        """選択したモデルを.envのDEFAULT_MODEL_NAMEに設定"""
        new_model = self.selected_model.get()
        try:
            write_model_name_to_env(new_model)
            self.current_model_name = new_model
            self._update_button_states()
            self.model_label.config(text=f"現在モデル名: {new_model}")
            self._log_message(f'[モデル確定] .env の DEFAULT_MODEL_NAME を "{new_model}" に更新しました\n')
            messagebox.showinfo("モデル確定", f'デフォルトモデルを "{new_model}" に設定しました')
        except Exception as e:
            self._log_message(f"[エラー] モデル名の更新に失敗: {e}\n")
            messagebox.showerror("エラー", f"モデル名の更新に失敗しました:\n{e}")

    def _update_button_states(self):
        match = self.selected_model.get() == self.current_model_name
        for widget in self.control_widgets:
            widget.config(state=tk.NORMAL if match else tk.DISABLED)

    def _log_message(self, message):
        """スレッドセーフなログ出力"""

        def update():
            self.log_text.insert(tk.END, message)
            self.log_text.see(tk.END)

        if threading.current_thread() is threading.main_thread():
            update()
        else:
            self.root.after(0, update)

    def _update_widgets_state(self, state):
        """スレッドセーフなウィジェット状態更新"""

        def update():
            for widget in self.control_widgets:
                widget.config(state=state)

        self.root.after(0, update)

    def _on_edit_settings_click(self):
        """詳細設定編集GUIを開く"""
        try:
            from src.ui.settings_gui_editor import open_settings_editor

            open_settings_editor(self.selected_model.get())
            self._log_message(f"[設定編集] {self.selected_model.get()} の詳細設定を開きました\n")
        except Exception as e:
            self._log_message(f"[エラー] 設定編集GUI起動失敗: {e}\n")
            import traceback

            self._log_message(traceback.format_exc() + "\n")
            messagebox.showerror("エラー", f"設定編集GUIの起動に失敗しました:\n{e}")

    def _on_edit_settings_file_click(self):
        """設定ファイルを直接エディタで開く（旧機能）"""
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        try:
            os.system(f'"{settings_path}"')
            self._log_message(f"[ファイル編集] {settings_path} を開きました\n")
        except Exception as e:
            self._log_message(f"[エラー] ファイル編集失敗: {e}\n")
            messagebox.showerror("エラー", f"設定ファイルの編集に失敗しました:\n{e}")

    def _on_edit_env_click(self):
        """環境変数編集GUIを開く"""
        try:
            from src.ui.env_gui_editor import open_env_editor

            open_env_editor()
            self._log_message("[環境変数編集] 環境変数編集GUIを開きました\n")
        except Exception as e:
            self._log_message(f"[エラー] 環境変数編集GUI起動失敗: {e}\n")
            import traceback

            self._log_message(traceback.format_exc() + "\n")
            messagebox.showerror("エラー", f"環境変数編集GUIの起動に失敗しました:\n{e}")

    def _on_edit_env_file_click(self):
        """環境変数ファイル(.env)を直接エディタで開く（旧機能）"""
        env_path = ".env"
        if not os.path.exists(env_path):
            # .envファイルが存在しない場合は.env.exampleからコピー
            response = messagebox.askyesno(
                ".envファイルが存在しません",
                ".env.exampleから.envファイルを作成しますか？\n\n" "作成後、エディタで開きます。",
            )
            if response:
                try:
                    import shutil

                    shutil.copy(".env.example", ".env")
                    self._log_message("[.env作成] .env.exampleから.envを作成しました\n")
                    messagebox.showinfo("作成成功", ".envファイルを作成しました")
                except Exception as e:
                    self._log_message(f"[エラー] .env作成失敗: {e}\n")
                    messagebox.showerror("エラー", f".envファイルの作成に失敗しました:\n{e}")
                    return
            else:
                return

        # .envファイルをエディタで開く
        try:
            os.system(f'"{env_path}"')
            self._log_message(f"[.env編集] {env_path} を開きました\n")
            messagebox.showinfo(
                "環境変数編集",
                "環境変数ファイル(.env)を編集しました。\n\n"
                "変更を反映するには:\n"
                "1. ファイルを保存\n"
                "2. アプリケーションを再起動\n"
                "3. APIサーバーは /restart_engine で再起動",
            )
        except Exception as e:
            self._log_message(f"[エラー] .env編集失敗: {e}\n")
            messagebox.showerror("エラー", f".envファイルの編集に失敗しました:\n{e}")

    def _on_validate_settings_click(self):
        """設定ファイルを検証（環境変数の状態も表示）"""
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        self._log_message(f"\n[設定検証開始] {settings_path}\n")
        self._log_message("=" * 60 + "\n")

        try:
            loader = SettingsLoader(settings_path)
            self._log_message("✓ 設定ファイルの読み込み成功\n\n")

            # 環境変数をインポート
            from src.config import env_loader

            # ===== モデル設定 (settings.py固有) =====
            self._log_message("【モデル設定】 settings.py で管理\n")
            self._log_message("-" * 60 + "\n")
            self._log_message(f"  IMAGE_SIZE: {loader.get_variable('IMAGE_SIZE')}\n")
            self._log_message(f"  FEATURE_DEPTH: {loader.get_variable('FEATURE_DEPTH')}\n")
            self._log_message(f"  SAVE_FORMAT: {loader.get_variable('SAVE_FORMAT')}\n")
            self._log_message(f"  PCA_VARIANCE: {loader.get_variable('PCA_VARIANCE')}\n")
            self._log_message(f"  ENABLE_AUGMENT: {loader.get_variable('ENABLE_AUGMENT')}\n\n")

            # ===== 異常検出しきい値 =====
            self._log_message("【異常検出しきい値】\n")
            self._log_message("-" * 60 + "\n")
            self._log_message(f"  Z_SCORE_THRESHOLD: {loader.get_variable('Z_SCORE_THRESHOLD')}\n")
            self._log_message(f"  Z_AREA_THRESHOLD: {loader.get_variable('Z_AREA_THRESHOLD')}\n")
            self._log_message(f"  Z_MAX_THRESHOLD: {loader.get_variable('Z_MAX_THRESHOLD')}\n\n")

            # ===== 実行環境設定 (.envで上書き可能) =====
            self._log_message("【実行環境設定】 .env で上書き可能\n")
            self._log_message("-" * 60 + "\n")

            # GPU設定の詳細表示
            use_gpu_settings = loader.module.USE_GPU if hasattr(loader.module, "USE_GPU") else None
            use_gpu_actual = loader.get_variable("USE_GPU")
            use_gpu_env = env_loader.USE_GPU

            if use_gpu_settings is not None and use_gpu_settings != use_gpu_actual:
                self._log_message(
                    f"  USE_GPU: {use_gpu_actual} ⚠️ [.env={use_gpu_env} が settings.py={use_gpu_settings} を上書き]\n"
                )
            else:
                self._log_message(f"  USE_GPU: {use_gpu_actual}")
                if use_gpu_settings is None:
                    self._log_message(" [.envから読み込み]\n")
                else:
                    self._log_message(" [settings.pyのデフォルト値]\n")

            # GPU_DEVICE_IDの表示
            gpu_device_settings = loader.module.GPU_DEVICE_ID if hasattr(loader.module, "GPU_DEVICE_ID") else None
            gpu_device_actual = loader.get_variable("GPU_DEVICE_ID")
            gpu_device_env = env_loader.GPU_DEVICE_ID

            if gpu_device_settings is not None and gpu_device_settings != gpu_device_actual:
                self._log_message(
                    f"  GPU_DEVICE_ID: {gpu_device_actual} ⚠️ [.env={gpu_device_env} が settings.py={gpu_device_settings} を上書き]\n"
                )
            else:
                self._log_message(f"  GPU_DEVICE_ID: {gpu_device_actual}\n")

            # その他の実行環境設定
            self._log_message(f"  USE_MIXED_PRECISION: {loader.get_variable('USE_MIXED_PRECISION')}\n")
            self._log_message(f"  MAX_CACHE_IMAGE: {loader.get_variable('MAX_CACHE_IMAGE')}\n")
            self._log_message(f"  NG_IMAGE_SAVE: {loader.get_variable('NG_IMAGE_SAVE')}\n\n")

            # ===== 環境設定 (.envのみ) =====
            self._log_message("【環境設定】 .env のみで管理\n")
            self._log_message("-" * 60 + "\n")
            self._log_message(f"  DEFAULT_MODEL_NAME: {env_loader.DEFAULT_MODEL_NAME}\n")
            self._log_message(f"  LOG_LEVEL: {env_loader.LOG_LEVEL}\n")
            self._log_message(f"  LOG_DIR: {env_loader.LOG_DIR}\n")
            self._log_message(f"  API_SERVER_HOST: {env_loader.API_SERVER_HOST}\n")
            self._log_message(f"  API_SERVER_PORT: {env_loader.API_SERVER_PORT}\n")
            self._log_message(f"  API_CLIENT_HOST: {env_loader.API_CLIENT_HOST}\n")
            self._log_message(f"  API_CLIENT_PORT: {env_loader.API_CLIENT_PORT}\n\n")

            # ===== 詳細検証 =====
            self._log_message("【設定検証】\n")
            self._log_message("=" * 60 + "\n")
            is_valid, errors = loader.validate_model_settings()

            if is_valid:
                self._log_message("✓ 設定ファイルは正常です\n\n")
                messagebox.showinfo("検証成功", "設定ファイルは正常です")
            else:
                self._log_message("✗ 設定ファイルにエラーがあります:\n")
                for error in errors:
                    self._log_message(f"  - {error}\n")
                self._log_message("\n")
                messagebox.showerror("検証失敗", "設定ファイルにエラーがあります:\n\n" + "\n".join(errors))

        except FileNotFoundError as e:
            self._log_message(f"✗ エラー: {e}\n\n")
            messagebox.showerror("エラー", str(e))
        except Exception as e:
            self._log_message(f"✗ 予期しないエラー: {e}\n\n")
            import traceback

            self._log_message(traceback.format_exc())
            messagebox.showerror("エラー", f"予期しないエラー: {e}")

    def _validate_settings_silent(self, settings_path: str) -> bool:
        """設定を静かに検証（戻り値: 検証成功かどうか）"""
        try:
            loader = SettingsLoader(settings_path)
            is_valid, errors = loader.validate_model_settings()

            if not is_valid:
                self._log_message("\n[警告] 設定ファイルに問題があります:\n")
                for error in errors:
                    self._log_message(f"  - {error}\n")
                self._log_message("\n")

            return is_valid
        except Exception as e:
            self._log_message(f"\n[警告] 設定検証エラー: {e}\n\n")
            return False

    def _on_affine_point_click(self):
        """アフィン座標取得を実行（直接インポート）"""
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")

        def task():
            self._update_widgets_state(tk.DISABLED)
            self._log_message("[アフィン座標取得開始]\n")
            self._log_message(f"使用設定: {settings_path}\n")

            try:
                # 直接インポートして実行
                from src.ui.projection_point_selector import ProjectionPointSelector

                selector = ProjectionPointSelector()
                points = selector.select_points()

                if points:
                    self._log_message("取得した座標:\n")
                    for i, (x, y) in enumerate(points, 1):
                        self._log_message(f"  点{i}: ({x}, {y})\n")
                    self._log_message("[実行完了]\n\n")
                else:
                    self._log_message("[キャンセルまたはエラー]\n\n")

            except Exception as e:
                self._log_message(f"[エラー] {e}\n")
                import traceback

                self._log_message(traceback.format_exc())

            finally:
                self.root.after(0, self._update_button_states)

        threading.Thread(target=task, daemon=True).start()

    def _on_train_button_click(self):
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")

        # 学習実行前に設定を検証
        if not self._validate_settings_silent(settings_path):
            response = messagebox.askyesno(
                "設定に問題があります", "設定ファイルに問題がありますが、学習を続行しますか？"
            )
            if not response:
                self._log_message("[学習中止] ユーザーによりキャンセルされました\n\n")
                return

        script_path = os.path.join("src", "model", "pipeline", "create.py")
        self._run_script_async(script_path, settings_path)

    def _on_inference_button_click(self):
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")

        # 推論実行前に設定を検証
        if not self._validate_settings_silent(settings_path):
            response = messagebox.askyesno(
                "設定に問題があります", "設定ファイルに問題がありますが、推論を続行しますか？"
            )
            if not response:
                self._log_message("[推論中止] ユーザーによりキャンセルされました\n\n")
                return

        script_path = os.path.join("src", "model", "pipeline", "inference.py")
        self._run_script_async(script_path, settings_path)

    def _run_script_async(self, script_path, settings_path):
        def task():
            # ボタンを無効化（メインスレッドで実行）
            self._update_widgets_state(tk.DISABLED)

            self._log_message(f"[実行開始] {script_path}\n")
            self._log_message(f"使用設定: {settings_path}\n")

            try:
                process = subprocess.Popen(
                    [sys.executable, script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    cwd=os.path.abspath("."),
                )
                for line in process.stdout:
                    self._log_message(line)

                process.wait()
                self._log_message("[実行完了]\n\n")

            except Exception as e:
                self._log_message(f"[エラー] {e}\n")

            finally:
                # ボタン状態を復元（メインスレッドで実行）
                self.root.after(0, self._update_button_states)

        threading.Thread(target=task, daemon=True).start()

    def on_close(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join("settings", "gui_log", f"{timestamp}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(self.log_text.get("1.0", tk.END))
        self.root.destroy()


def launch_gui():
    root = tk.Tk()
    app = ModelLauncherGUI(root)  # noqa: F841
    app.confirm_button.config(state=tk.NORMAL)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
