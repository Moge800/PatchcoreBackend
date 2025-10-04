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

MAIN_SETTINGS_PATH = os.path.join("settings", "main_settings.py")


def read_model_name_from_main_settings():
    try:
        with open(MAIN_SETTINGS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("MODEL_NAME"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    except Exception as e:
        print(f"Error reading MODEL_NAME: {e}")
    return None


def write_model_name_to_main_settings(new_model_name):
    try:
        with open(MAIN_SETTINGS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        with open(MAIN_SETTINGS_PATH, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip().startswith("MODEL_NAME"):
                    f.write(f'MODEL_NAME = "{new_model_name}"\n')
                else:
                    f.write(line)
    except Exception as e:
        print(f"Error writing MODEL_NAME: {e}")


class ModelLauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PatchCoreモデル操作GUI")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.model_base_dir = os.path.join("settings", "models")
        self.model_dirs = [
            d for d in os.listdir(self.model_base_dir) if os.path.isdir(os.path.join(self.model_base_dir, d))
        ]
        self.has_models = len(self.model_dirs) > 0
        self.selected_model = tk.StringVar(value=self.model_dirs[0] if self.has_models else "")
        self.current_model_name = read_model_name_from_main_settings()

        self._setup_widgets()
        self._update_button_states()

    def _setup_widgets(self):
        self.model_label = tk.Label(self.root, text=f"現在モデル名: {self.selected_model.get()}", font=("Arial", 14))
        self.model_label.pack(pady=10)

        dropdown_frame = tk.Frame(self.root)
        dropdown_frame.pack(pady=5)

        self.model_dropdown = ttk.Combobox(
            dropdown_frame, textvariable=self.selected_model, values=self.model_dirs, state="readonly", width=30
        )
        self.model_dropdown.pack(side=tk.LEFT)
        self.model_dropdown.bind("<<ComboboxSelected>>", self._on_model_select)

        self.confirm_button = tk.Button(dropdown_frame, text="確定", command=self._on_confirm_model)
        self.confirm_button.pack(side=tk.LEFT, padx=5)

        self.log_text = scrolledtext.ScrolledText(self.root, width=80, height=20, font=("Consolas", 10))
        self.log_text.pack(pady=10)

        self.edit_button = tk.Button(
            self.root, text="settings編集", font=("Arial", 12), width=20, command=self._on_edit_settings_click
        )
        self.edit_button.pack(pady=5)

        self.validate_button = tk.Button(
            self.root,
            text="設定検証",
            font=("Arial", 12),
            width=20,
            command=self._on_validate_settings_click,
            bg="#e3f2fd",
        )
        self.validate_button.pack(pady=5)

        self.affine_button = tk.Button(
            self.root, text="アフィン座標取得", font=("Arial", 12), width=20, command=self._on_affine_point_click
        )
        self.affine_button.pack(pady=5)

        self.train_button = tk.Button(
            self.root, text="学習実行", font=("Arial", 12), width=20, command=self._on_train_button_click
        )
        self.train_button.pack(pady=5)

        self.inference_button = tk.Button(
            self.root, text="テスト推論実行", font=("Arial", 12), width=20, command=self._on_inference_button_click
        )
        self.inference_button.pack(pady=5)

        self.control_widgets = [
            self.edit_button,
            self.validate_button,
            self.affine_button,
            self.train_button,
            self.inference_button,
            self.confirm_button,
        ]

    def _on_model_select(self, event):
        self.model_label.config(text=f"現在モデル名: {self.selected_model.get()}")
        self._update_button_states()

    def _on_confirm_model(self):
        new_model = self.selected_model.get()
        write_model_name_to_main_settings(new_model)
        self.current_model_name = new_model
        self._update_button_states()
        self.model_label.config(text=f"現在モデル名: {new_model}")
        self._log_message(f'[モデル名更新] MODEL_NAME = "{new_model}"\n')

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
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        os.system(f'"{settings_path}"')

    def _on_validate_settings_click(self):
        """設定ファイルを検証"""
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        self._log_message(f"\n[設定検証開始] {settings_path}\n")
        self._log_message("=" * 60 + "\n")

        try:
            loader = SettingsLoader(settings_path)
            self._log_message("✓ 設定ファイルの読み込み成功\n\n")

            # 基本設定の表示
            self._log_message("基本設定:\n")
            self._log_message(f"  IMAGE_SIZE: {loader.get_variable('IMAGE_SIZE')}\n")
            self._log_message(f"  FEATURE_DEPTH: {loader.get_variable('FEATURE_DEPTH')}\n")
            self._log_message(f"  SAVE_FORMAT: {loader.get_variable('SAVE_FORMAT')}\n")
            self._log_message(f"  USE_GPU: {loader.get_variable('USE_GPU')}\n\n")

            # しきい値の表示
            self._log_message("しきい値設定:\n")
            self._log_message(f"  Z_SCORE_THRESHOLD: {loader.get_variable('Z_SCORE_THRESHOLD')}\n")
            self._log_message(f"  Z_AREA_THRESHOLD: {loader.get_variable('Z_AREA_THRESHOLD')}\n")
            self._log_message(f"  Z_MAX_THRESHOLD: {loader.get_variable('Z_MAX_THRESHOLD')}\n\n")

            # 詳細検証
            is_valid, errors = loader.validate_model_settings()

            self._log_message("=" * 60 + "\n")
            if is_valid:
                self._log_message("✓ 設定ファイルは正常です\n\n")
                messagebox.showinfo("検証成功", "設定ファイルは正常です")
            else:
                self._log_message("✗ 設定ファイルにエラーがあります:\n")
                for error in errors:
                    self._log_message(f"  - {error}\n")
                self._log_message("\n")
                messagebox.showerror("検証失敗", f"設定ファイルにエラーがあります:\n\n" + "\n".join(errors))

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
        script_path = os.path.join("src", "ui", "projection_point_selector.py")
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        self._run_script_async(script_path, settings_path)

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
