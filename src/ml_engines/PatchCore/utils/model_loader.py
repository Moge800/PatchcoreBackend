import os
import torch
import pickle


def load_model_and_assets(model_dir: str, save_format: str):
    model = torch.jit.load(os.path.join(model_dir, "model.pt"))
    model.eval()

    bank_path = "memory_bank_compressed.pkl" if save_format == "compressed" else "memory_bank.pkl"
    with open(os.path.join(model_dir, bank_path), "rb") as f:
        memory_bank = pickle.load(f)
    with open(os.path.join(model_dir, "pca.pkl"), "rb") as f:
        pca = pickle.load(f)
    with open(os.path.join(model_dir, "pixel_stats.pkl"), "rb") as f:
        pixel_mean, pixel_std = pickle.load(f)

    return model, memory_bank, pca, pixel_mean, pixel_std
