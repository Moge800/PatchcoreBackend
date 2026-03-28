from typing import Optional, Tuple

import cv2
import torch
import numpy as np
from src.ml_engines.PatchCore.utils.inference_utils import (
    preprocess_cv2,
    load_image_unicode_path,
)
from src.ml_engines.PatchCore.utils.score_utils import evaluate_z_score_map, is_ok_z


class GpuAssets:
    """PCA変換・距離計算用のGPUテンソルをキャッシュするコンテナ"""

    def __init__(self, pca, memory_bank: np.ndarray, device: torch.device) -> None:
        self.pca_components_t = torch.from_numpy(
            pca.components_.T.astype(np.float32)
        ).to(device)
        self.pca_mean_t = torch.from_numpy(pca.mean_.astype(np.float32)).to(device)
        self.bank_mean_t = torch.from_numpy(
            memory_bank.mean(axis=0).astype(np.float32)
        ).to(device)


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
    device: Optional[torch.device] = None,
    gpu_assets: Optional[GpuAssets] = None,
) -> Tuple[np.ndarray, dict, bool]:
    image = load_image_unicode_path(image_path)
    inputs = preprocess_cv2(image, affine_points, image_size)

    if device is not None:
        inputs = inputs.to(device)

    with torch.no_grad():
        fmap = model(inputs)
        patches = fmap.squeeze(0).permute(1, 2, 0).reshape(-1, fmap.size(1))

        if gpu_assets is not None:
            # GPU上でPCA変換と距離計算
            patches = patches.float()
            patches_pca = (
                patches - gpu_assets.pca_mean_t
            ) @ gpu_assets.pca_components_t
            scores = torch.norm(patches_pca - gpu_assets.bank_mean_t, dim=1)
            score_map = scores.reshape(fmap.shape[2], fmap.shape[3]).cpu().numpy()
        else:
            # CPU fallback
            patches_np = patches.cpu().numpy() if patches.is_cuda else patches.numpy()
            patches_np = pca.transform(patches_np)
            scores_np = np.linalg.norm(patches_np - memory_bank.mean(axis=0), axis=1)
            score_map = scores_np.reshape(fmap.shape[2], fmap.shape[3])

        raw_score_map = cv2.resize(score_map, image_size, interpolation=cv2.INTER_CUBIC)

    pixel_std_safe = np.where(pixel_std == 0, 1e-6, pixel_std)
    z_score_map = (raw_score_map - pixel_mean) / pixel_std_safe

    z_stats = evaluate_z_score_map(z_score_map, z_score_threshold)
    is_ok = is_ok_z(z_stats, z_area_threshold, z_max_threshold)

    z_score_map_vis = np.clip(z_score_map, 0, 5.0)
    z_score_map_vis = (z_score_map_vis / 5.0 * 255).astype(np.uint8)
    heatmap = cv2.applyColorMap(z_score_map_vis, cv2.COLORMAP_JET)

    input_img = inputs.squeeze(0).permute(1, 2, 0)
    if input_img.is_cuda:
        input_img = input_img.cpu()
    input_img = (input_img.numpy() * 255).astype(np.uint8)

    overlay = cv2.addWeighted(
        cv2.cvtColor(input_img, cv2.COLOR_RGB2BGR),
        0.6,
        heatmap,
        0.4,
        0,
    )
    overlay = cv2.resize(overlay, [400, 400])

    return overlay, z_stats, is_ok
