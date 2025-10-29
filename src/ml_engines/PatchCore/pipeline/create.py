import os
import cv2
import torch
import torch.nn as nn
import numpy as np
import pickle
from sklearn.decomposition import PCA
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image, ImageFilter, ImageEnhance
from src.config.settings_loader import SettingsLoader
from src.config import env_loader
from src.ml_engines.PatchCore.utils.inference_utils import preprocess_cv2, load_image_unicode_path
from src.ml_engines.PatchCore.utils.device_utils import get_device, clear_gpu_cache
from src.utils.logger import setup_logger

logger = setup_logger("model_creator", log_dir="logs/model")


class FeatureExtractor(nn.Module):
    def __init__(self, depth: int = 1):
        super().__init__()
        resnet = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)

        self.layer0 = nn.Sequential(resnet.conv1, resnet.bn1, resnet.relu, resnet.maxpool)
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2 if depth >= 2 else None
        self.layer3 = resnet.layer3 if depth >= 3 else None
        self.layer4 = resnet.layer4 if depth >= 4 else None
        self.depth = depth

    def forward(self, x):
        x = self.layer0(x)
        x = self.layer1(x)
        if self.depth >= 2:
            x = self.layer2(x)
        if self.depth >= 3:
            x = self.layer3(x)
        if self.depth >= 4:
            x = self.layer4(x)
        return x


def run_creator():
    MODEL_NAME = env_loader.DEFAULT_MODEL_NAME
    DATASET_DIR = os.path.join("datasets", MODEL_NAME)
    NORMAL_DIR = os.path.join(DATASET_DIR, "normal")
    AUGMENTED_DIR = os.path.join(DATASET_DIR, "normal_augmented")
    MODEL_DIR = os.path.join("models", MODEL_NAME)
    SETTINGS_PATH = os.path.join("settings", "models", MODEL_NAME, "settings.py")
    os.makedirs(MODEL_DIR, exist_ok=True)

    loader = SettingsLoader(SETTINGS_PATH)
    AFFINE_POINTS = loader.get_variable("AFFINE_POINTS")
    IMAGE_SIZE = loader.get_variable("IMAGE_SIZE")
    PCA_VARIANCE = loader.get_variable("PCA_VARIANCE")
    ENABLE_AUGMENT = loader.get_variable("ENABLE_AUGMENT")
    SAVE_FORMAT = loader.get_variable("SAVE_FORMAT")
    FEATURE_DEPTH = loader.get_variable("FEATURE_DEPTH")

    # GPU設定の読み込み
    USE_GPU = loader.get_variable("USE_GPU")
    GPU_DEVICE_ID = loader.get_variable("GPU_DEVICE_ID")
    USE_MIXED_PRECISION = loader.get_variable("USE_MIXED_PRECISION")

    # デバイス設定
    device = get_device(USE_GPU, GPU_DEVICE_ID)

    if ENABLE_AUGMENT and not os.path.isdir(AUGMENTED_DIR):
        os.makedirs(AUGMENTED_DIR, exist_ok=True)
        i = 0
        for fname in os.listdir(NORMAL_DIR):
            if fname.lower().endswith(".png"):
                path = os.path.join(NORMAL_DIR, fname)
                image = Image.open(path).convert("RGB")
                blurred = image.filter(ImageFilter.GaussianBlur(radius=2))
                enhanced = ImageEnhance.Brightness(blurred).enhance(1.2)
                enhanced = ImageEnhance.Contrast(enhanced).enhance(1.3)
                enhanced = ImageEnhance.Color(enhanced).enhance(1.1)
                enhanced.save(os.path.join(AUGMENTED_DIR, f"aug_{fname}"))
                sharp_img = ImageEnhance.Sharpness(image).enhance(1.2)
                sharp_img.save(os.path.join(AUGMENTED_DIR, f"aug_s_{fname}"))
                i += 1
        logger.info(f"Data augmentation completed: {i} images created")

    image_paths = []
    for subdir in [NORMAL_DIR, AUGMENTED_DIR] if ENABLE_AUGMENT else [NORMAL_DIR]:
        for fname in os.listdir(subdir):
            if fname.lower().endswith(".png"):
                image_paths.append(os.path.join(subdir, fname))

    model = FeatureExtractor(FEATURE_DEPTH)
    model = model.to(device)  # モデルをGPUに移動
    model.eval()
    memory_bank = []

    # 混合精度演算の設定（新しいAPI）
    scaler = torch.amp.GradScaler("cuda") if USE_MIXED_PRECISION and device.type == "cuda" else None

    with torch.no_grad():
        for idx, path in enumerate(image_paths):
            image = load_image_unicode_path(path)
            inputs = preprocess_cv2(image, AFFINE_POINTS, IMAGE_SIZE)
            inputs = inputs.to(device)  # 入力をGPUに移動

            if scaler and USE_MIXED_PRECISION:
                with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                    fmap = model(inputs)
            else:
                fmap = model(inputs)

            patches = fmap.squeeze(0).permute(1, 2, 0).reshape(-1, fmap.size(1))

            sampling_ratio = 0.1
            patches_np = patches.cpu().numpy()

            if sampling_ratio < 1.0:
                sample_size = int(len(patches_np) * sampling_ratio)
                indices = np.random.choice(len(patches_np), sample_size, replace=False)
                patches_np = patches_np[indices]

            memory_bank.append(patches_np)

            if idx % 10 == 0:
                logger.info(f"Training in progress... {idx+1}/{len(image_paths)}")

    memory_bank = np.concatenate(memory_bank, axis=0)
    pca = PCA(n_components=PCA_VARIANCE)
    memory_bank_compressed = pca.fit_transform(memory_bank)

    if SAVE_FORMAT == "compressed":
        with open(os.path.join(MODEL_DIR, "memory_bank_compressed.pkl"), "wb") as f:
            pickle.dump(memory_bank_compressed, f)
    else:
        with open(os.path.join(MODEL_DIR, "memory_bank.pkl"), "wb") as f:
            pickle.dump(memory_bank, f)

    with open(os.path.join(MODEL_DIR, "pca.pkl"), "wb") as f:
        pickle.dump(pca, f)

    # モデル保存時にCPUに移動してからトレース
    model_cpu = model.cpu()
    example_input = torch.randn(1, 3, *IMAGE_SIZE)  # CPUテンソル
    scripted_model = torch.jit.trace(model_cpu, example_input)
    scripted_model.save(os.path.join(MODEL_DIR, "model.pt"))
    logger.info(f"Model and memory bank ({SAVE_FORMAT}) saved to {MODEL_DIR}")

    # Zスコアマップ作成のためにモデルを再度GPUに移動
    model = model.to(device)

    score_maps = []
    with torch.no_grad():
        for idx, path in enumerate(image_paths):
            image = load_image_unicode_path(path)
            inputs = preprocess_cv2(image, AFFINE_POINTS, IMAGE_SIZE)
            inputs = inputs.to(device)  # 入力をGPUに移動

            if scaler and USE_MIXED_PRECISION:
                with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                    fmap = model(inputs)
            else:
                fmap = model(inputs)

            patches = fmap.squeeze(0).permute(1, 2, 0).reshape(-1, fmap.size(1)).cpu().numpy()
            patches = pca.transform(patches)
            scores = np.linalg.norm(patches - memory_bank_compressed.mean(axis=0), axis=1)
            score_map = scores.reshape(fmap.shape[2], fmap.shape[3])
            raw_score_map = cv2.resize(score_map, IMAGE_SIZE, interpolation=cv2.INTER_CUBIC)
            score_maps.append(raw_score_map)
            if idx % 10 == 0:
                logger.info(f"Creating Z-score map... {idx+1}/{len(image_paths)}")

    score_maps = np.stack(score_maps)
    pixel_mean = np.mean(score_maps, axis=0)
    pixel_std = np.std(score_maps, axis=0)

    with open(os.path.join(MODEL_DIR, "pixel_stats.pkl"), "wb") as f:
        pickle.dump((pixel_mean, pixel_std), f)

    logger.info("Pixel-wise Z-score statistics saved: pixel_stats.pkl")

    # GPU キャッシュクリア
    clear_gpu_cache()


if __name__ == "__main__":
    run_creator()
