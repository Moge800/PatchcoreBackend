import tkinter as tk
from tkinter import ttk, messagebox
import os
import re
import sys

# パスを追加してsrcモジュールをインポート可能にする
sys.path.insert(0, os.path.abspath("."))
from src.config.settings_loader import SettingsLoader


class SettingsGUIEditor:
    """設定ファイル用のGUIエディタ"""

    def __init__(self, root, model_name: str):
        self.root = root
        self.model_name = model_name
        self.settings_path = os.path.join("settings", "models", model_name, "settings.py")

        # 設定値を保持する辞書
        self.settings_vars = {}

        # ウィンドウ設定
        self.root.title(f"設定編集 - {model_name}")
        self.root.resizable(True, True)

        # 設定項目の定義
        self._define_setting_configs()

        # GUI構築
        self._setup_gui()

        # 現在の設定値を読み込み
        self._load_current_settings()

    def _define_setting_configs(self):
        """設定項目の定義（UI要素の種類、制約など）"""
        self.setting_configs = {
            "IMAGE_SIZE": {
                "type": "tuple_int",
                "label": "入力画像サイズ (幅, 高さ)",
                "description": "モデルへの入力画像サイズ。学習・推論時に画像をこのサイズにリサイズ",
                "default": (224, 224),
            },
            "TEST_DIR": {
                "type": "string",
                "label": "テスト画像フォルダ名",
                "description": "テスト推論対象の画像を格納するフォルダ名",
                "default": "test_image",
            },
            "ENABLE_AUGMENT": {
                "type": "boolean",
                "label": "データ拡張の有効化",
                "description": "学習時にぼかし・シャープなどの加工を加えた画像も使用するか",
                "default": True,
            },
            "Z_SCORE_THRESHOLD": {
                "type": "float",
                "label": "Zスコア画素値しきい値",
                "description": "画素単位で異常度を評価するための基準値。高いほど異常検出が厳しくなる",
                "min": 0.0,
                "max": 20.0,
                "step": 0.1,
                "default": 4.5,
            },
            "Z_AREA_THRESHOLD": {
                "type": "int",
                "label": "異常画素数許容上限",
                "description": "異常と判定された画素の数がこの値を超えるとNGと判定",
                "min": 0,
                "max": 10000,
                "default": 100,
            },
            "Z_MAX_THRESHOLD": {
                "type": "float",
                "label": "Zスコア最大値許容上限",
                "description": "Zスコアマップの中で最も高い値がこのしきい値を超えるとNG判定",
                "min": 0.0,
                "max": 50.0,
                "step": 0.1,
                "default": 10.0,
            },
            "FEATURE_DEPTH": {
                "type": "choice",
                "label": "モデルレイヤー深さ",
                "description": "浅いと高解像度で微細異常検出力が上がるがノイズに弱い。深いとノイズに強いが微細検出力が下がる",
                "choices": [1, 2, 3, 4],
                "default": 1,
            },
            "PCA_VARIANCE": {
                "type": "float",
                "label": "PCA分散保持割合",
                "description": "メモリバンクの次元削減で保持する分散割合。1.0に近いほど情報保持率が高い",
                "min": 0.1,
                "max": 1.0,
                "step": 0.01,
                "default": 0.95,
            },
            "SAVE_FORMAT": {
                "type": "choice",
                "label": "メモリバンク保存形式",
                "description": "compressed=PCAで次元削減された軽量形式、raw=元の特徴量をそのまま保存",
                "choices": ["compressed", "raw"],
                "default": "compressed",
            },
            "USE_GPU": {
                "type": "boolean",
                "label": "GPU使用",
                "description": "GPU計算を使用するか（.envで上書き可能）",
                "default": False,
            },
            "GPU_DEVICE_ID": {
                "type": "int",
                "label": "GPU デバイスID",
                "description": "使用するGPUのデバイスID（.envで上書き可能）",
                "min": 0,
                "max": 8,
                "default": 0,
            },
            "USE_MIXED_PRECISION": {
                "type": "boolean",
                "label": "混合精度計算使用",
                "description": "メモリ効率化のために混合精度計算を使用するか（.envで上書き可能）",
                "default": True,
            },
            "NG_IMAGE_SAVE": {
                "type": "boolean",
                "label": "NG画像保存",
                "description": "NG判定された画像を保存するか（.envで上書き可能）",
                "default": True,
            },
            "MAX_CACHE_IMAGE": {
                "type": "int",
                "label": "最大キャッシュ画像数",
                "description": "メモリに保持する最大画像数（.envで上書き可能）",
                "min": 100,
                "max": 5000,
                "default": 1200,
            },
        }

    def _setup_gui(self):
        """GUI要素を構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # スクロール可能なキャンバス
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # タイトル
        title_label = tk.Label(scrollable_frame, text=f"モデル設定: {self.model_name}", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 設定項目のフレーム
        self.settings_frame = ttk.Frame(scrollable_frame)
        self.settings_frame.pack(fill=tk.BOTH, expand=True)

        # 各設定項目のUI要素を作成
        self._create_setting_widgets()

        # ボタンフレーム
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # ボタン
        ttk.Button(button_frame, text="設定を読み直し", command=self._load_current_settings).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="デフォルトに戻す", command=self._reset_to_defaults).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="検証", command=self._validate_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="保存", command=self._save_settings, style="Accent.TButton").pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(button_frame, text="キャンセル", command=self.root.destroy).pack(side=tk.RIGHT)

        # レイアウト配置
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # マウスホイール対応
        self._bind_mousewheel(canvas)

    def _bind_mousewheel(self, canvas):
        """マウスホイールでスクロール"""

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _create_setting_widgets(self):
        """各設定項目のUI要素を作成"""
        row = 0

        for setting_name, config in self.setting_configs.items():
            # ラベルフレーム
            frame = ttk.LabelFrame(self.settings_frame, text=config["label"], padding=(10, 5))
            frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
            self.settings_frame.grid_columnconfigure(0, weight=1)

            # 説明ラベル
            desc_label = tk.Label(
                frame, text=config["description"], font=("Arial", 9), fg="gray", wraplength=400, justify=tk.LEFT
            )
            desc_label.pack(anchor="w", pady=(0, 5))

            # 設定値に応じたUI要素を作成
            widget_frame = ttk.Frame(frame)
            widget_frame.pack(fill=tk.X)

            if config["type"] == "boolean":
                var = tk.BooleanVar(value=config["default"])
                widget = ttk.Checkbutton(widget_frame, variable=var)
                widget.pack(anchor="w")

            elif config["type"] == "choice":
                var = tk.StringVar(value=str(config["default"]))
                widget = ttk.Combobox(
                    widget_frame,
                    textvariable=var,
                    values=[str(choice) for choice in config["choices"]],
                    state="readonly",
                    width=20,
                )
                widget.pack(anchor="w")

            elif config["type"] == "int":
                var = tk.IntVar(value=config["default"])
                widget_container = ttk.Frame(widget_frame)
                widget_container.pack(anchor="w")

                widget = tk.Spinbox(
                    widget_container,
                    from_=config.get("min", 0),
                    to=config.get("max", 999999),
                    textvariable=var,
                    width=15,
                )
                widget.pack(side=tk.LEFT)

                if "min" in config and "max" in config:
                    range_label = tk.Label(
                        widget_container, text=f"({config['min']} - {config['max']})", font=("Arial", 8), fg="gray"
                    )
                    range_label.pack(side=tk.LEFT, padx=(5, 0))

            elif config["type"] == "float":
                var = tk.DoubleVar(value=config["default"])
                widget_container = ttk.Frame(widget_frame)
                widget_container.pack(anchor="w")

                step = config.get("step", 0.1)
                widget = tk.Spinbox(
                    widget_container,
                    from_=config.get("min", 0.0),
                    to=config.get("max", 999.0),
                    increment=step,
                    textvariable=var,
                    width=15,
                    format="%.2f",
                )
                widget.pack(side=tk.LEFT)

                if "min" in config and "max" in config:
                    range_label = tk.Label(
                        widget_container, text=f"({config['min']} - {config['max']})", font=("Arial", 8), fg="gray"
                    )
                    range_label.pack(side=tk.LEFT, padx=(5, 0))

            elif config["type"] == "string":
                var = tk.StringVar(value=config["default"])
                widget = ttk.Entry(widget_frame, textvariable=var, width=30)
                widget.pack(anchor="w")

            elif config["type"] == "tuple_int":
                var = tk.StringVar(value=f"{config['default'][0]}, {config['default'][1]}")
                widget_container = ttk.Frame(widget_frame)
                widget_container.pack(anchor="w")

                tk.Label(widget_container, text="(").pack(side=tk.LEFT)
                widget = ttk.Entry(widget_container, textvariable=var, width=15)
                widget.pack(side=tk.LEFT)
                tk.Label(widget_container, text=") 形式: 幅, 高さ", font=("Arial", 8), fg="gray").pack(
                    side=tk.LEFT, padx=(5, 0)
                )

            # 変数を保存
            self.settings_vars[setting_name] = var
            row += 1

    def _load_current_settings(self):
        """現在の設定ファイルから値を読み込み"""
        try:
            if not os.path.exists(self.settings_path):
                messagebox.showerror("エラー", f"設定ファイルが見つかりません: {self.settings_path}")
                return

            loader = SettingsLoader(self.settings_path)

            for setting_name, var in self.settings_vars.items():
                try:
                    current_value = loader.get_variable(setting_name)
                    config = self.setting_configs[setting_name]

                    if config["type"] == "boolean":
                        var.set(bool(current_value))
                    elif config["type"] == "choice":
                        var.set(str(current_value))
                    elif config["type"] in ["int", "float"]:
                        var.set(current_value)
                    elif config["type"] == "string":
                        var.set(str(current_value))
                    elif config["type"] == "tuple_int":
                        if isinstance(current_value, (list, tuple)) and len(current_value) == 2:
                            var.set(f"{current_value[0]}, {current_value[1]}")
                        else:
                            var.set("224, 224")  # デフォルト

                except Exception as e:
                    print(f"Warning: Could not load {setting_name}: {e}")
                    # デフォルト値を設定
                    self._set_default_value(setting_name, var)

            messagebox.showinfo("完了", "設定を読み込みました")

        except Exception as e:
            messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {e}")

    def _set_default_value(self, setting_name: str, var):
        """デフォルト値を設定"""
        config = self.setting_configs[setting_name]
        default = config["default"]

        if config["type"] == "tuple_int":
            var.set(f"{default[0]}, {default[1]}")
        else:
            var.set(default)

    def _reset_to_defaults(self):
        """すべての設定をデフォルト値に戻す"""
        if messagebox.askyesno("確認", "すべての設定をデフォルト値に戻しますか？"):
            for setting_name, var in self.settings_vars.items():
                self._set_default_value(setting_name, var)
            messagebox.showinfo("完了", "すべての設定をデフォルト値にリセットしました")

    def _validate_settings(self):
        """設定値を検証"""
        errors = []

        for setting_name, var in self.settings_vars.items():
            config = self.setting_configs[setting_name]

            try:
                if config["type"] == "tuple_int":
                    value_str = var.get().strip()
                    if not re.match(r"^\s*\d+\s*,\s*\d+\s*$", value_str):
                        errors.append(f"{config['label']}: 正しい形式で入力してください (例: 224, 224)")
                        continue
                    width, height = map(int, [x.strip() for x in value_str.split(",")])
                    if width <= 0 or height <= 0:
                        errors.append(f"{config['label']}: 正の整数を指定してください")

                elif config["type"] in ["int", "float"]:
                    value = var.get()
                    min_val = config.get("min")
                    max_val = config.get("max")

                    if min_val is not None and value < min_val:
                        errors.append(f"{config['label']}: {min_val}以上の値を入力してください")
                    if max_val is not None and value > max_val:
                        errors.append(f"{config['label']}: {max_val}以下の値を入力してください")

                elif config["type"] == "string":
                    value = var.get().strip()
                    if not value:
                        errors.append(f"{config['label']}: 空文字は指定できません")

            except Exception as e:
                errors.append(f"{config['label']}: 無効な値です ({e})")

        if errors:
            messagebox.showerror("検証エラー", "以下のエラーがあります:\n\n" + "\n".join(errors))
            return False
        else:
            messagebox.showinfo("検証成功", "すべての設定値が正常です")
            return True

    def _save_settings(self):
        """設定をファイルに保存"""
        if not self._validate_settings():
            return

        try:
            # 現在の設定ファイルを読み込み
            with open(self.settings_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 各設定値を更新
            for setting_name, var in self.settings_vars.items():
                config = self.setting_configs[setting_name]

                # 新しい値を取得
                if config["type"] == "boolean":
                    new_value = var.get()
                elif config["type"] == "choice":
                    raw_value = var.get()
                    if config["choices"] and isinstance(config["choices"][0], int):
                        new_value = int(raw_value)
                    else:
                        new_value = f'"{raw_value}"'
                elif config["type"] == "int":
                    new_value = var.get()
                elif config["type"] == "float":
                    new_value = var.get()
                elif config["type"] == "string":
                    new_value = f'"{var.get().strip()}"'
                elif config["type"] == "tuple_int":
                    value_str = var.get().strip()
                    width, height = map(int, [x.strip() for x in value_str.split(",")])
                    new_value = f"({width}, {height})"

                # 正規表現で該当行を置換
                pattern = rf"^(\s*{setting_name}\s*=\s*).*$"
                replacement = rf"\g<1>{new_value}"
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

            # ファイルに書き戻し
            with open(self.settings_path, "w", encoding="utf-8") as f:
                f.write(content)

            messagebox.showinfo("保存完了", "設定を保存しました")
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("保存エラー", f"設定の保存に失敗しました: {e}")


def open_settings_editor(model_name: str):
    """設定エディタを開く（外部から呼び出し用）"""
    root = tk.Toplevel()
    editor = SettingsGUIEditor(root, model_name)
    root.focus_set()
    root.grab_set()  # モーダルダイアログにする
    return editor


if __name__ == "__main__":
    # テスト用
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示

    model_name = "example_model"
    editor = open_settings_editor(model_name)

    root.mainloop()
