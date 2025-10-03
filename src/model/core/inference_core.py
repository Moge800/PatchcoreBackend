import cv2
import torch
import numpy as np
from src.model.utils.inference_utils import preprocess_cv2, load_image_unicode_path
from src.model.utils.score_utils import evaluate_z_score_map, is_ok_z


def run_inference_on_image(
    image_path: str,
    model,
    memory_bank,
    pca,
    pixel_mean,
    pixel_std,
    affine_points,
    image_size,
    z_score_threshold,
    z_area_threshold,
    z_max_threshold,
):
    image = load_image_unicode_path(image_path)
    inputs = preprocess_cv2(image, affine_points, image_size)
    with torch.no_grad():
        fmap = model(inputs)
        patches = fmap.squeeze(0).permute(1, 2, 0).reshape(-1, fmap.size(1)).numpy()
        patches = pca.transform(patches)
        scores = np.linalg.norm(patches - memory_bank.mean(axis=0), axis=1)
        score_map = scores.reshape(fmap.shape[2], fmap.shape[3])
        raw_score_map = cv2.resize(score_map, image_size, interpolation=cv2.INTER_CUBIC)

    pixel_std_safe = np.where(pixel_std == 0, 1e-6, pixel_std)
    z_score_map = (raw_score_map - pixel_mean) / pixel_std_safe

    z_stats = evaluate_z_score_map(z_score_map, z_score_threshold)
    is_ok = is_ok_z(z_stats, z_area_threshold, z_max_threshold)

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

    return overlay, z_stats, is_ok
