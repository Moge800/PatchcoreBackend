import os
import glob
from datetime import datetime
import cv2
from sklearn.decomposition import PCA  # noqa: F401
from src.config.settings_loader import SettingsLoader
from src.config import env_loader
import logging
from src.ml_engines.PatchCore.utils.inference_utils import save_overlay_image
from src.ml_engines.PatchCore.utils.model_loader import load_model_and_assets
from src.ml_engines.PatchCore.core.inference_core import run_inference_on_image

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_inference():
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

    image_paths = glob.glob(os.path.join(SETTINGS_DIR, TEST_DIR, "*.png"))
    if not image_paths:
        raise FileNotFoundError("No test images found.")

    model, memory_bank, pca, pixel_mean, pixel_std = load_model_and_assets(MODEL_DIR, SAVE_FORMAT)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_save_dir = os.path.join(SETTINGS_DIR, "execute", "test", timestamp)
    os.makedirs(img_save_dir, exist_ok=True)

    overlay_list = []
    for i, image_path in enumerate(image_paths):
        overlay, z_stats, is_ok = run_inference_on_image(
            image_path,
            model,
            memory_bank,
            pca,
            pixel_mean,
            pixel_std,
            AFFINE_POINTS,
            IMAGE_SIZE,
            Z_SCORE_THRESHOLD,
            Z_AREA_THRESHOLD,
            Z_MAX_THRESHOLD,
        )

        label = "OK" if is_ok else "NG"
        logging.info("-" * 10)
        logging.info(f"{image_path}")
        logging.info(f"z_sum={z_stats['total']:.2f}, z_max={z_stats['maxval']:.2f}, z_area={z_stats['area']}")
        logging.info(f"is_ok_z={is_ok}")
        logging.info("-" * 10)

        color = (0, 255, 0) if label == "OK" else (0, 0, 255)
        cv2.putText(
            overlay, f"[{label}] {os.path.basename(image_path)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
        )

        save_overlay_image(overlay, img_save_dir, i, label, image_path)
        overlay_list.append(overlay)

    cv2.imshow("Anomaly Map", cv2.hconcat(overlay_list))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_inference()
