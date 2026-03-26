import numpy as np

def normalize_domain(x: np.ndarray, bounds: tuple) -> np.ndarray:
    """归一化到[-1, 1]"""
    x_min, x_max = bounds
    return 2 * (x - x_min) / (x_max - x_min) - 1

def parse_boundary_condition(bc_config: dict):
    """解析边界条件配置"""
    return bc_config
