import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import os
import sys
from datetime import datetime

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
        self.log_text.insert(tk.END, f'[モデル名更新] MODEL_NAME = "{new_model}"\n')
        self.log_text.see(tk.END)

    def _update_button_states(self):
        match = self.selected_model.get() == self.current_model_name
        for widget in self.control_widgets:
            widget.config(state=tk.NORMAL if match else tk.DISABLED)

    def _on_edit_settings_click(self):
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        os.system(f'"{settings_path}"')

    def _on_affine_point_click(self):
        script_path = os.path.join("src", "ui", "projection_point_selector.py")
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        self._run_script_async(script_path, settings_path)

    def _on_train_button_click(self):
        script_path = os.path.join("src", "model", "pipeline", "create.py")
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        self._run_script_async(script_path, settings_path)

    def _on_inference_button_click(self):
        script_path = os.path.join("src", "model", "pipeline", "inference.py")
        settings_path = os.path.join("settings", "models", self.selected_model.get(), "settings.py")
        self._run_script_async(script_path, settings_path)

    def _run_script_async(self, script_path, settings_path):
        def task():
            for widget in self.control_widgets:
                widget.config(state=tk.DISABLED)

            self.log_text.insert(tk.END, f"[実行開始] {script_path}\n")
            self.log_text.insert(tk.END, f"使用設定: {settings_path}\n")
            self.log_text.see(tk.END)

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
                    self.log_text.insert(tk.END, line)
                    self.log_text.see(tk.END)
                process.wait()
                self.log_text.insert(tk.END, "[実行完了]\n\n")
            except Exception as e:
                self.log_text.insert(tk.END, f"[エラー] {e}\n")
            finally:
                self._update_button_states()
                self.log_text.see(tk.END)

        threading.Thread(target=task).start()

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
