import numpy as np

def compute_error(predicted: np.ndarray, exact: np.ndarray) -> dict:
    """计算误差指标"""
    l2_error = np.linalg.norm(predicted - exact) / np.linalg.norm(exact)
    return {"l2_relative_error": float(l2_error)}

def export_to_vtk(x, y, u, filename: str):
    """导出VTK格式"""
    # TODO: 实现VTK导出
    pass
