import numpy as np


def evaluate_z_score_map(z_map: np.ndarray, z_score_threshold: float) -> dict:
    total = np.sum(z_map)
    area = np.sum(z_map > z_score_threshold)
    maxval = np.max(z_map)
    mean = np.mean(z_map)
    std = np.std(z_map)
    minval = np.min(z_map)
    percentile_95 = np.percentile(z_map, 95)
    area_ratio = area / z_map.size

    return {
        "total": total,
        "area": area,
        "maxval": maxval,
        "mean": mean,
        "std": std,
        "minval": minval,
        "percentile_95": percentile_95,
        "area_ratio": area_ratio,
    }


def is_ok_z(
    stats: dict, z_area_threshold: int = 100, z_max_threshold: float = 5.0
) -> bool:
    """
    Zスコア統計情報に基づいて異常かどうかを判定する。

    Args:
        stats (dict): evaluate_z_score_map() の戻り値。
        z_area_threshold (int): 異常画素数の許容上限。
        z_max_threshold (float): Zスコアの最大値の許容上限。

    Returns:
        bool: 異常がなければ True（OK）、異常があれば False（NG）。
    """

    return stats["area"] < z_area_threshold and stats["maxval"] < z_max_threshold
