import os


def torch_runtime_summary() -> dict:
    try:
        import torch
    except ImportError:
        return {
            "available": False,
            "device": "unavailable",
            "cuda_available": False,
            "reason": "PyTorch is not installed in the active backend environment.",
        }

    requested_device = (os.getenv("PINNSOLVER_TORCH_DEVICE") or "auto").lower()
    cuda_available = bool(torch.cuda.is_available())

    if requested_device == "cpu":
        device = "cpu"
    elif requested_device == "cuda" and cuda_available:
        device = "cuda"
    elif cuda_available:
        device = "cuda"
    else:
        device = "cpu"

    return {
        "available": True,
        "device": device,
        "cuda_available": cuda_available,
        "requested_device": requested_device,
        "torch_version": torch.__version__,
    }
