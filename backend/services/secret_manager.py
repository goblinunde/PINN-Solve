from pathlib import Path
import os
import sys


BASE_DIR = Path(__file__).resolve().parent.parent
RUST_EXTENSION_DIR = BASE_DIR.parent / "pinn-core" / "target" / "release"

if str(RUST_EXTENSION_DIR) not in sys.path:
    sys.path.insert(0, str(RUST_EXTENSION_DIR))


def _load_rust_secret_module():
    try:
        import pinn_core
    except ImportError as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "Rust secret manager is unavailable. Build pinn-core first so secrets can be encrypted safely."
        ) from exc
    return pinn_core


def encrypt_secret(value: str | None, *, persist: bool = True) -> str | None:
    if not value or not persist:
        return None
    module = _load_rust_secret_module()
    return module.encrypt_secret(value)


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    module = _load_rust_secret_module()
    return module.decrypt_secret(value)
