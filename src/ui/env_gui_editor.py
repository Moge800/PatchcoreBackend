import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil


class EnvGUIEditor:
    """環境変数設定ファイル(.env)用のGUIエディタ"""

    def __init__(self, root: tk.Toplevel):
        self.root = root
        self.env_path = ".env"
        self.env_example_path = ".env.example"

        # 設定値を保持する辞書
        self.env_vars: dict[str, tk.StringVar | tk.BooleanVar | tk.IntVar] = {}

        # ウィンドウ設定
        self.root.title("環境変数設定編集")
        self.root.geometry("550x800")
        self.root.resizable(False, True)

        # 環境変数項目の定義
        self._define_env_configs()

        # GUI構築
        self._setup_gui()

        # 現在の環境変数値を読み込み
        self._load_current_env()

    def _define_env_configs(self):
        """環境変数項目の定義（UI要素の種類、制約など）"""
        self.env_configs = {
            # アプリケーション設定
            "APP_NAME": {
                "type": "string",
                "label": "アプリケーション名",
                "description": "アプリケーションの名前を設定",
                "default": "PatchCoreBackend",
                "category": "アプリケーション設定",
            },
            "APP_VERSION": {
                "type": "string",
                "label": "アプリケーションバージョン",
                "description": "アプリケーションのバージョン番号",
                "default": "1.0.0",
                "category": "アプリケーション設定",
            },
            "DEBUG": {
                "type": "boolean",
                "label": "デバッグモード",
                "description": "デバッグ出力を有効にするかどうか",
                "default": False,
                "category": "アプリケーション設定",
            },
            # APIサーバー設定
            "API_SERVER_HOST": {
                "type": "choice",
                "label": "APIサーバーホスト",
                "description": "サーバーがバインドするアドレス。0.0.0.0=外部アクセス可、127.0.0.1=ローカルのみ",
                "choices": ["0.0.0.0", "127.0.0.1", "localhost"],
                "default": "0.0.0.0",
                "category": "APIサーバー設定",
            },
            "API_SERVER_PORT": {
                "type": "int",
                "label": "APIサーバーポート",
                "description": "サーバーがリッスンするポート番号",
                "min": 1000,
                "max": 65535,
                "default": 8000,
                "category": "APIサーバー設定",
            },
            "API_RELOAD": {
                "type": "boolean",
                "label": "API自動リロード",
                "description": "コード変更時の自動リロード（開発用）",
                "default": False,
                "category": "APIサーバー設定",
            },
            "API_WORKERS": {
                "type": "int",
                "label": "APIワーカー数",
                "description": "並列実行するワーカープロセス数",
                "min": 1,
                "max": 16,
                "default": 1,
                "category": "APIサーバー設定",
            },
            # APIクライアント設定
            "API_CLIENT_HOST": {
                "type": "choice",
                "label": "APIクライアントホスト",
                "description": "クライアントが接続する先のアドレス",
                "choices": ["127.0.0.1", "localhost", "0.0.0.0"],
                "default": "127.0.0.1",
                "category": "APIクライアント設定",
            },
            "API_CLIENT_PORT": {
                "type": "int",
                "label": "APIクライアントポート",
                "description": "クライアントが接続するポート番号",
                "min": 1000,
                "max": 65535,
                "default": 8000,
                "category": "APIクライアント設定",
            },
            # モデル設定
            "DEFAULT_MODEL_NAME": {
                "type": "string",
                "label": "デフォルトモデル名",
                "description": "起動時に使用するデフォルトのモデル名",
                "default": "example_model",
                "category": "モデル設定",
            },
            # ログ設定
            "LOG_LEVEL": {
                "type": "choice",
                "label": "ログレベル",
                "description": "出力するログの詳細度",
                "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "default": "INFO",
                "category": "ログ設定",
            },
            "LOG_DIR": {
                "type": "string",
                "label": "ログディレクトリ",
                "description": "ログファイルを保存するディレクトリ",
                "default": "logs",
                "category": "ログ設定",
            },
            # GPU設定
            "USE_GPU": {
                "type": "boolean",
                "label": "GPU使用",
                "description": "GPU計算を使用するかどうか",
                "default": False,
                "category": "GPU設定",
            },
            "GPU_DEVICE_ID": {
                "type": "int",
                "label": "GPU デバイスID",
                "description": "使用するGPUのデバイスID",
                "min": 0,
                "max": 8,
                "default": 0,
                "category": "GPU設定",
            },
            "USE_MIXED_PRECISION": {
                "type": "boolean",
                "label": "混合精度計算",
                "description": "メモリ効率化のために混合精度計算を使用",
                "default": True,
                "category": "GPU設定",
            },
            # CPU最適化設定
            "CPU_THREADS": {
                "type": "int",
                "label": "CPU スレッド数",
                "description": "使用するCPUスレッド数",
                "min": 1,
                "max": 32,
                "default": 4,
                "category": "CPU最適化設定",
            },
            "CPU_MEMORY_EFFICIENT": {
                "type": "boolean",
                "label": "CPU メモリ効率化",
                "description": "CPUメモリ効率化モードを有効にする",
                "default": True,
                "category": "CPU最適化設定",
            },
            # データ設定
            "DATA_DIR": {
                "type": "string",
                "label": "データディレクトリ",
                "description": "データセットを格納するディレクトリ",
                "default": "datasets",
                "category": "データ設定",
            },
            "MODEL_DIR": {
                "type": "string",
                "label": "モデルディレクトリ",
                "description": "学習済みモデルを格納するディレクトリ",
                "default": "models",
                "category": "データ設定",
            },
            "SETTINGS_DIR": {
                "type": "string",
                "label": "設定ディレクトリ",
                "description": "設定ファイルを格納するディレクトリ",
                "default": "settings",
                "category": "データ設定",
            },
            # キャッシュ設定
            "MAX_CACHE_IMAGES": {
                "type": "int",
                "label": "最大キャッシュ画像数",
                "description": "メモリに保持する最大画像数",
                "min": 100,
                "max": 5000,
                "default": 1200,
                "category": "キャッシュ設定",
            },
            "CACHE_TTL": {
                "type": "int",
                "label": "キャッシュ有効期間",
                "description": "キャッシュの有効期間（秒）",
                "min": 60,
                "max": 86400,
                "default": 3600,
                "category": "キャッシュ設定",
            },
            # NG画像保存設定
            "NG_IMAGE_SAVE": {
                "type": "boolean",
                "label": "NG画像保存",
                "description": "NG判定された画像を保存するかどうか",
                "default": True,
                "category": "NG画像保存設定",
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

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # タイトル
        title_label = tk.Label(
            scrollable_frame, text="環境変数設定", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # .envファイル状態表示
        self.status_label = tk.Label(
            scrollable_frame, text="", font=("Arial", 10), fg="blue"
        )
        self.status_label.pack(pady=(0, 10))
        self._update_status_label()

        # 設定項目のフレーム
        self.settings_frame = ttk.Frame(scrollable_frame)
        self.settings_frame.pack(fill=tk.BOTH, expand=True)

        # カテゴリ別に設定項目のUI要素を作成
        self._create_env_widgets()

        # ボタンフレーム
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # ボタン
        ttk.Button(button_frame, text=".env作成", command=self._create_env_file).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(
            button_frame, text="設定を読み直し", command=self._load_current_env
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame, text="デフォルトに戻す", command=self._reset_to_defaults
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="検証", command=self._validate_env).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(
            button_frame, text="保存", command=self._save_env, style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="キャンセル", command=self.root.destroy).pack(
            side=tk.RIGHT
        )

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

    def _create_env_widgets(self):
        """各環境変数項目のUI要素をカテゴリ別に作成"""
        # カテゴリごとにグループ化
        categories = {}
        for env_name, config in self.env_configs.items():
            category = config.get("category", "その他")
            if category not in categories:
                categories[category] = []
            categories[category].append((env_name, config))

        row = 0

        for category, items in categories.items():
            # カテゴリラベル
            category_frame = ttk.LabelFrame(
                self.settings_frame, text=f"【{category}】", padding=(10, 5)
            )
            category_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=10)
            self.settings_frame.grid_columnconfigure(0, weight=1)

            item_row = 0
            for env_name, config in items:
                # 設定項目フレーム
                item_frame = ttk.Frame(category_frame)
                item_frame.grid(row=item_row, column=0, sticky="ew", padx=5, pady=5)
                category_frame.grid_columnconfigure(0, weight=1)

                # ラベル
                label = tk.Label(
                    item_frame, text=config["label"], font=("Arial", 10, "bold")
                )
                label.grid(row=0, column=0, sticky="w")

                # 説明
                desc_label = tk.Label(
                    item_frame,
                    text=config["description"],
                    font=("Arial", 9),
                    fg="gray",
                    wraplength=400,
                )
                desc_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

                # UI要素
                widget_frame = ttk.Frame(item_frame)
                widget_frame.grid(row=2, column=0, sticky="w")

                if config["type"] == "boolean":
                    var = tk.BooleanVar(value=config["default"])
                    widget = ttk.Checkbutton(widget_frame, variable=var)
                    widget.pack(anchor="w")

                elif config["type"] == "choice":
                    var = tk.StringVar(value=str(config["default"]))
                    widget = ttk.Combobox(
                        widget_frame,
                        textvariable=var,
                        values=config["choices"],
                        state="readonly",
                        width=25,
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
                            widget_container,
                            text=f"({config['min']} - {config['max']})",
                            font=("Arial", 8),
                            fg="gray",
                        )
                        range_label.pack(side=tk.LEFT, padx=(5, 0))

                elif config["type"] == "string":
                    var = tk.StringVar(value=config["default"])
                    widget = ttk.Entry(widget_frame, textvariable=var, width=30)
                    widget.pack(anchor="w")

                # 変数を保存
                self.env_vars[env_name] = var
                item_row += 1

            row += 1

    def _update_status_label(self):
        """ファイル状態ラベルを更新"""
        if os.path.exists(self.env_path):
            self.status_label.config(text=f"✓ {self.env_path} が存在します", fg="green")
        else:
            self.status_label.config(
                text=f"⚠ {self.env_path} が存在しません", fg="orange"
            )

    def _create_env_file(self):
        """.envファイルを.env.exampleから作成"""
        if os.path.exists(self.env_path):
            result = messagebox.askyesno(
                "確認", f"{self.env_path} は既に存在します。上書きしますか？"
            )
            if not result:
                return

        if not os.path.exists(self.env_example_path):
            messagebox.showerror("エラー", f"{self.env_example_path} が見つかりません")
            return

        try:
            shutil.copy(self.env_example_path, self.env_path)
            self._update_status_label()
            self._load_current_env()
            messagebox.showinfo("完了", f"{self.env_path} を作成しました")
        except Exception as e:
            messagebox.showerror("エラー", f"ファイル作成に失敗しました: {e}")

    def _load_current_env(self):
        """現在の環境変数ファイルから値を読み込み"""
        try:
            self._update_status_label()

            if not os.path.exists(self.env_path):
                # .envが存在しない場合はデフォルト値を使用
                for env_name, var in self.env_vars.items():
                    config = self.env_configs[env_name]
                    self._set_default_value(env_name, var)
                messagebox.showwarning(
                    "警告",
                    f"{self.env_path} が存在しないため、デフォルト値を使用しています",
                )
                return

            # .envファイルから現在の値を読み取り
            env_values = {}
            with open(self.env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_values[key.strip()] = value.strip()

            # UI要素に値を設定
            for env_name, var in self.env_vars.items():
                if env_name in env_values:
                    config = self.env_configs[env_name]
                    value = env_values[env_name]

                    try:
                        if config["type"] == "boolean":
                            var.set(value.lower() in ("true", "1", "yes"))
                        elif config["type"] in ["choice", "string"]:
                            var.set(value)
                        elif config["type"] == "int":
                            var.set(int(value))
                    except ValueError:
                        # 変換失敗時はデフォルト値を使用
                        self._set_default_value(env_name, var)
                else:
                    # 値が存在しない場合はデフォルト値を使用
                    self._set_default_value(env_name, var)

            messagebox.showinfo("完了", "環境変数を読み込みました")

        except Exception as e:
            messagebox.showerror("エラー", f"環境変数の読み込みに失敗しました: {e}")

    def _set_default_value(self, env_name: str, var):
        """デフォルト値を設定"""
        config = self.env_configs[env_name]
        default = config["default"]
        var.set(default)

    def _reset_to_defaults(self):
        """すべての環境変数をデフォルト値に戻す"""
        if messagebox.askyesno("確認", "すべての環境変数をデフォルト値に戻しますか？"):
            for env_name, var in self.env_vars.items():
                self._set_default_value(env_name, var)
            messagebox.showinfo(
                "完了", "すべての環境変数をデフォルト値にリセットしました"
            )

    def _validate_env(self):
        """環境変数値を検証"""
        errors = []

        for env_name, var in self.env_vars.items():
            config = self.env_configs[env_name]

            try:
                if config["type"] == "int":
                    value = var.get()
                    min_val = config.get("min")
                    max_val = config.get("max")

                    if min_val is not None and value < min_val:
                        errors.append(
                            f"{config['label']}: {min_val}以上の値を入力してください"
                        )
                    if max_val is not None and value > max_val:
                        errors.append(
                            f"{config['label']}: {max_val}以下の値を入力してください"
                        )

                elif config["type"] == "string":
                    value = var.get().strip()
                    if not value:
                        errors.append(f"{config['label']}: 空文字は指定できません")

            except Exception as e:
                errors.append(f"{config['label']}: 無効な値です ({e})")

        if errors:
            messagebox.showerror(
                "検証エラー", "以下のエラーがあります:\n\n" + "\n".join(errors)
            )
            return False
        else:
            messagebox.showinfo("検証成功", "すべての環境変数値が正常です")
            return True

    def _save_env(self):
        """環境変数をファイルに保存"""
        if not self._validate_env():
            return

        try:
            # 新しい.envファイルの内容を生成
            lines = []
            lines.append("# 環境変数設定ファイル")
            lines.append("# このファイルはGUIエディタにより自動生成されました")
            lines.append("")
            lines.append("PYTHONPATH=.")
            lines.append("")

            # カテゴリごとにグループ化して出力
            categories = {}
            for env_name, config in self.env_configs.items():
                category = config.get("category", "その他")
                if category not in categories:
                    categories[category] = []
                categories[category].append(env_name)

            for category, env_names in categories.items():
                lines.append(f"# {category}")
                for env_name in env_names:
                    var = self.env_vars[env_name]
                    config = self.env_configs[env_name]

                    # 値を取得
                    if config["type"] == "boolean":
                        value = "True" if var.get() else "False"
                    else:
                        value = str(var.get())

                    lines.append(f"{env_name}={value}")
                lines.append("")

            # ファイルに書き込み
            with open(self.env_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self._update_status_label()
            messagebox.showinfo(
                "保存完了",
                "環境変数を保存しました\n\n変更を反映するにはアプリケーションの再起動が必要です",
            )
            self.root.destroy()

        except Exception as e:
            messagebox.showerror("保存エラー", f"環境変数の保存に失敗しました: {e}")


def open_env_editor():
    """環境変数エディタを開く（外部から呼び出し用）"""
    root = tk.Toplevel()
    editor = EnvGUIEditor(root)
    root.focus_set()
    root.grab_set()  # モーダルダイアログにする
    return editor


if __name__ == "__main__":
    # テスト用
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示

    editor = open_env_editor()

    root.mainloop()
