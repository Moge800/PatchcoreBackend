import os
import glob
from datetime import datetime
import torch
import cv2
import numpy as np
import pickle
from sklearn.decomposition import PCA
from src.config.settings_loader import SettingsLoader
from src.config import env_loader
import logging
from src.model.utils.inference_utils import preprocess_cv2, evaluate_z_score_map, is_ok_z

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    MODEL_NAME = env_loader.DEFAULT_MODEL_NAME
    MODEL_DIR = os.path.join("models", MODEL_NAME)
    SETTINGS_DIR = os.path.join("settings", "models", MODEL_NAME)
    SETTINGS_PATH = os.path.join(SETTINGS_DIR, "settings.py")
    loader = SettingsLoader(SETTINGS_PATH)

    AFFINE_POINTS = loader.get_variable("AFFINE_POINTS")
    IMAGE_SIZE = loader.get_variable("IMAGE_SIZE")
    SAVE_FORMAT = loader.get_variable("SAVE_FORMAT")
    TEST_DIR = loader.get_variable("TEST_DIR")
    Z_SCORE_THRESHOLD = loader.get_variable("Z_SCORE_THRESHOLD")
    Z_AREA_THRESHOLD = loader.get_variable("Z_AREA_THRESHOLD")
    Z_MAX_THRESHOLD = loader.get_variable("Z_MAX_THRESHOLD")

    image_paths = glob.glob(os.path.join(MODEL_DIR, TEST_DIR, "*.png"))
    if len(image_paths) == 0:
        raise FileNotFoundError("No test images found.")

    model = torch.jit.load(os.path.join(MODEL_DIR, "model.pt"))
    model.eval()

    bank_path = "memory_bank_compressed.pkl" if SAVE_FORMAT == "compressed" else "memory_bank.pkl"
    with open(os.path.join(MODEL_DIR, bank_path), "rb") as f:
        memory_bank = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "pca.pkl"), "rb") as f:
        pca: PCA = pickle.load(f)
    with open(os.path.join(MODEL_DIR, "pixel_stats.pkl"), "rb") as f:
        pixel_mean, pixel_std = pickle.load(f)

    overlay_list = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_save_dir = os.path.join(SETTINGS_DIR, "execute", timestamp)
    os.makedirs(img_save_dir)

    for i, image_path in enumerate(image_paths):
        inputs = preprocess_cv2(image_path, AFFINE_POINTS, IMAGE_SIZE)
        with torch.no_grad():
            fmap = model(inputs)
            patches = fmap.squeeze(0).permute(1, 2, 0).reshape(-1, fmap.size(1)).numpy()
            patches = pca.transform(patches)
            scores = np.linalg.norm(patches - memory_bank.mean(axis=0), axis=1)
            score_map = scores.reshape(fmap.shape[2], fmap.shape[3])
            raw_score_map = cv2.resize(score_map, IMAGE_SIZE, interpolation=cv2.INTER_CUBIC)

        pixel_std_safe = np.where(pixel_std == 0, 1e-6, pixel_std)
        z_score_map = (raw_score_map - pixel_mean) / pixel_std_safe

        z_score_map_vis = np.clip(z_score_map, 0, 5.0)
        z_score_map_vis = (z_score_map_vis / 5.0 * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(z_score_map_vis, cv2.COLORMAP_JET)

        overlay = cv2.addWeighted(
            cv2.cvtColor(inputs.squeeze(0).permute(1, 2, 0).numpy() * 255, cv2.COLOR_RGB2BGR).astype(np.uint8),
            0.6,
            heatmap,
            0.4,
            0,
        )
        overlay = cv2.resize(overlay, [400, 400])

        z_stats = evaluate_z_score_map(z_score_map, Z_SCORE_THRESHOLD)
        is_ok = is_ok_z(z_stats, Z_AREA_THRESHOLD, Z_MAX_THRESHOLD)
        logging.info("-" * 10)
        logging.info(f"{image_path}")
        logging.info(f"z_sum={z_stats['total']:.2f}, z_max={z_stats['maxval']:.2f}, z_area={z_stats['area']}")
        logging.info(f"is_ok_z={is_ok}")
        logging.info("-" * 10)

        label = "OK" if is_ok else "NG"
        color = (0, 255, 0) if label == "OK" else (0, 0, 255)
        cv2.putText(
            overlay, f"[{label}] {os.path.basename(image_path)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )
        overlay_list.append(overlay)
        cv2.imwrite(os.path.join(img_save_dir, f"{i:03}_{label}.png"), overlay)

    overlay = cv2.hconcat(overlay_list)
    cv2.imshow("Anomaly Map", overlay)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
