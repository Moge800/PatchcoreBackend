# 射影変換に使用する4点座標（左上→右上→右下→左下の順）
# 画像の台形領域を矩形に変換するための基準点。GUIで選択した順に記録する。
AFFINE_POINTS = [[152, 96], [422, 98], [494, 361], [33, 352]]

# モデルへの入力画像サイズ（幅, 高さ）
# 学習・推論時に画像をこのサイズにリサイズする。モデルの設計に合わせて調整。
IMAGE_SIZE = (224, 224)

# テスト画像フォルダ名（settings/models/[MODEL_NAME]/[TEST_DIR] に配置）
# テスト推論対象の画像を格納するフォルダ名
TEST_DIR = "test_image"

# データ拡張の有効化（Trueで拡張画像も使用）
# 学習時にぼかし・シャープなどの加工を加えた画像も使用するかどうか。
# モデル学習のコア設定のためsettings.pyで管理
ENABLE_AUGMENT = True

# -----NG判定設定-----
# Zスコアマップの画素値しきい値（これを超える画素を異常とみなす）
# 画素単位で異常度を評価するための基準値。高いほど異常検出が厳しくなる。
Z_SCORE_THRESHOLD = 4.5

# 異常画素数の許容上限（これを超えるとNG判定）
# 異常と判定された画素の数がこの値を超えると、をNGと判定する。
Z_AREA_THRESHOLD = 100

# Zスコアの最大値の許容上限（これを超えるとNG判定）
# Zスコアマップの中で最も高い値がこのしきい値を超えるとNGと判定する。
Z_MAX_THRESHOLD = 10.0

# モデルレイヤーの深さ [1〜4]
# 浅いと高解像度で微細異常検出力が上がるがノイズに弱くなる
# 深いと低解像度になりノイズに強くなるが微細検出力が下がる
# 学習・推論コストは深くなるほど重くなる（演算が増えるため）
FEATURE_DEPTH = 1

# PCAによる次元削減で保持する分散割合（0.0〜1.0）
# メモリバンクの次元を削減する際に、どれだけの情報を保持するかを指定。
# 1.0に近いほど情報保持率が高くなるが、計算コストも増える。
# 異常検出精度に直接関与するためsettings.pyで管理
PCA_VARIANCE = 0.95

# メモリバンクの保存形式（"compressed" または "raw"）
# "compressed" はPCAで次元削減された軽量形式、"raw" は元の特徴量をそのまま保存。
SAVE_FORMAT = "compressed"

# -----実行環境設定（環境変数でオーバーライド可能）-----
# これらの設定は .env ファイルで上書きできます
# 以下はデフォルト値で、環境変数が設定されている場合はそちらが優先されます

# GPU設定（.envのUSE_GPU, GPU_DEVICE_ID, USE_MIXED_PRECISIONでオーバーライド可能）
USE_GPU = False
GPU_DEVICE_ID = 0
USE_MIXED_PRECISION = True

# CPU最適化設定（.envのCPU_THREADS, CPU_MEMORY_EFFICIENTでオーバーライド可能）
CPU_OPTIMIZATION = {
    "threads": 4,
    "memory_efficient": True,
}

# inference_engine設定（.envのNG_IMAGE_SAVE, MAX_CACHE_IMAGESでオーバーライド可能）
NG_IMAGE_SAVE = True
MAX_CACHE_IMAGE = 1200
