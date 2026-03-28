#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"

PROFILE="${1:-auto}"

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-base.txt

detect_gpu() {
  command -v nvidia-smi >/dev/null 2>&1
}

install_cpu_torch() {
  echo "[PINN-Solve] Installing CPU-only PyTorch backend"
  python -m pip install --index-url https://download.pytorch.org/whl/cpu torch
}

install_gpu_torch() {
  echo "[PINN-Solve] Installing GPU PyTorch backend"
  python -m pip install torch
}

case "$PROFILE" in
  cpu)
    install_cpu_torch
    ;;
  gpu)
    install_gpu_torch
    ;;
  auto)
    if detect_gpu; then
      echo "[PINN-Solve] NVIDIA GPU detected"
      install_gpu_torch
    else
      echo "[PINN-Solve] No NVIDIA GPU detected"
      install_cpu_torch
    fi
    ;;
  *)
    echo "Usage: ./install-deps.sh [auto|cpu|gpu]"
    exit 1
    ;;
esac

echo "[PINN-Solve] Dependency installation completed"
