import math
import os
from dataclasses import dataclass

import numpy as np

try:
    import torch
    import torch.nn as nn
except ImportError:  # pragma: no cover - optional dependency at runtime
    torch = None
    nn = None


@dataclass
class LayerSpec:
    size: int
    activation: str
    residual: bool


def _activation_module(name: str):
    if nn is None:
        raise ImportError("PyTorch is required for the Python training backend.")

    key = (name or "tanh").lower()
    if key == "relu":
        return nn.ReLU()
    if key == "sigmoid":
        return nn.Sigmoid()
    if key == "softplus":
        return nn.Softplus()
    if key == "gelu":
        return nn.GELU()
    if key == "linear":
        return nn.Identity()
    return nn.Tanh()


class ResidualMLPBlock:
    def __init__(self, in_features: int, spec: LayerSpec):
        import torch.nn as nn

        self.linear = nn.Linear(in_features, spec.size)
        self.activation = _activation_module(spec.activation)
        self.use_residual = spec.residual and in_features == spec.size

    def __call__(self, x):
        out = self.activation(self.linear(x))
        if self.use_residual:
            out = out + x
        return out


class MLPBackbone(nn.Module if nn is not None else object):
    def __init__(self, input_dim: int, hidden_layers: list[LayerSpec], output_dim: int, output_activation: str):
        super().__init__()
        self.hidden_layers = hidden_layers
        current_dim = input_dim
        self.layers = nn.ModuleList()

        current_dim = input_dim
        for spec in hidden_layers:
            linear = nn.Linear(current_dim, spec.size)
            activation = _activation_module(spec.activation)
            self.layers.append(nn.ModuleDict({
                "linear": linear,
                "activation": activation,
            }))
            current_dim = spec.size

        self.output = nn.Linear(current_dim, output_dim)
        self.output_activation = _activation_module(output_activation)

    def forward(self, x):
        for spec, layer in zip(self.hidden_layers, self.layers):
            out = layer["activation"](layer["linear"](x))
            if spec.residual and out.shape[-1] == x.shape[-1]:
                out = out + x
            x = out
        return self.output_activation(self.output(x))


class CNNBackbone(nn.Module if nn is not None else object):
    def __init__(self, input_dim: int, hidden_layers: list[LayerSpec], output_dim: int, output_activation: str):
        super().__init__()
        channels = [max(4, spec.size) for spec in hidden_layers] or [32, 32]
        self.hidden_layers = hidden_layers or [LayerSpec(size=channels[0], activation="tanh", residual=False)]
        self.proj = nn.Linear(input_dim, input_dim)
        self.blocks = nn.ModuleList()
        current_channels = 1

        for index, channels_out in enumerate(channels):
            spec = self.hidden_layers[min(index, len(self.hidden_layers) - 1)]
            block = nn.ModuleDict({
                "conv": nn.Conv1d(current_channels, channels_out, kernel_size=3, padding=1),
                "activation": _activation_module(spec.activation),
            })
            self.blocks.append(block)
            current_channels = channels_out

        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Linear(current_channels, output_dim)
        self.output_activation = _activation_module(output_activation)

    def forward(self, x):
        x = self.proj(x)
        x = x.unsqueeze(1)
        for index, block in enumerate(self.blocks):
            out = block["activation"](block["conv"](x))
            spec = self.hidden_layers[min(index, len(self.hidden_layers) - 1)]
            if spec.residual and out.shape == x.shape:
                out = out + x
            x = out
        x = self.pool(x).squeeze(-1)
        return self.output_activation(self.head(x))


class RecurrentBackbone(nn.Module if nn is not None else object):
    def __init__(self, architecture: str, hidden_layers: list[LayerSpec], output_dim: int, output_activation: str):
        super().__init__()
        recurrent_map = {
            "rnn": nn.RNN,
            "gru": nn.GRU,
            "lstm": nn.LSTM,
        }
        recurrent_cls = recurrent_map[architecture]
        self.hidden_layers = hidden_layers or [LayerSpec(size=32, activation="tanh", residual=False)]
        self.blocks = nn.ModuleList()
        input_size = 1
        for spec in self.hidden_layers:
            self.blocks.append(
                nn.ModuleDict({
                    "recurrent": recurrent_cls(input_size=input_size, hidden_size=spec.size, batch_first=True),
                    "activation": _activation_module(spec.activation),
                })
            )
            input_size = spec.size
        self.head = nn.Linear(input_size, output_dim)
        self.output_activation = _activation_module(output_activation)

    def forward(self, x):
        x = x.unsqueeze(-1)
        for spec, block in zip(self.hidden_layers, self.blocks):
            recurrent = block["recurrent"]
            out, hidden = recurrent(x)
            out = block["activation"](out)
            if spec.residual and out.shape == x.shape:
                out = out + x
            x = out

        pooled = x.mean(dim=1)
        return self.output_activation(self.head(pooled))


def build_model(network_config: dict):
    if nn is None:
        raise ImportError("PyTorch is required for the Python training backend.")

    architecture = (network_config.get("architecture") or "mlp").lower()
    input_dim = int(network_config.get("input_dim") or 2)
    output_dim = int(network_config.get("output_dim") or 1)
    output_activation = network_config.get("output_activation") or "linear"
    hidden_layers = [
        LayerSpec(
            size=max(1, int(layer.get("size", 32))),
            activation=layer.get("activation") or "tanh",
            residual=bool(layer.get("residual", False)),
        )
        for layer in (network_config.get("hidden_layers") or [])
    ]

    if architecture == "cnn":
        backbone = CNNBackbone(input_dim, hidden_layers, output_dim, output_activation)
    elif architecture in {"rnn", "gru", "lstm"}:
        backbone = RecurrentBackbone(architecture, hidden_layers, output_dim, output_activation)
    else:
        backbone = MLPBackbone(input_dim, hidden_layers, output_dim, output_activation)

    class Model(nn.Module):
        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, x):
            return self.inner.forward(x)

    return Model(backbone), architecture


def _gradient(outputs, inputs):
    import torch

    return torch.autograd.grad(
        outputs,
        inputs,
        grad_outputs=torch.ones_like(outputs),
        create_graph=True,
        retain_graph=True,
    )[0]


def _laplace_residual(model, points):
    values = model(points)
    grad = _gradient(values, points)
    u_xx = _gradient(grad[:, :1], points)[:, :1]
    u_yy = _gradient(grad[:, 1:2], points)[:, 1:2]
    return u_xx + u_yy


def _poisson_source(points, source_type: str):
    import torch

    x = points[:, :1]
    y = points[:, 1:2]
    if source_type == "one":
        return torch.ones_like(x)
    if source_type == "sine":
        return torch.sin(math.pi * x) * torch.sin(math.pi * y)
    return torch.zeros_like(x)


def _poisson_residual(model, points, source_type: str):
    return _laplace_residual(model, points) - _poisson_source(points, source_type)


def _heat_residual(model, points, alpha: float):
    values = model(points)
    grad = _gradient(values, points)
    u_x = grad[:, :1]
    u_t = grad[:, 1:2]
    u_xx = _gradient(u_x, points)[:, :1]
    return u_t - alpha * u_xx


def _burgers_residual(model, points, viscosity: float):
    values = model(points)
    grad = _gradient(values, points)
    u_x = grad[:, :1]
    u_t = grad[:, 1:2]
    u_xx = _gradient(u_x, points)[:, :1]
    return u_t + values * u_x - viscosity * u_xx


def _sample_collocation_points(n_points: int, input_dim: int, device):
    import torch

    return torch.rand((max(16, n_points), input_dim), device=device, dtype=torch.float32)


def _sample_boundary_points(kind: str, n_boundary: int, config: dict, device):
    import torch

    count = max(8, n_boundary)
    if kind in {"laplace_2d", "poisson_2d"}:
        base = torch.rand((count, 2), device=device, dtype=torch.float32)
        side = torch.randint(0, 4, (count,), device=device)
        base[side == 0, 0] = 0.0
        base[side == 1, 0] = 1.0
        base[side == 2, 1] = 0.0
        base[side == 3, 1] = 1.0
        targets = torch.zeros((count, 1), device=device, dtype=torch.float32)
        return base, targets

    x = torch.rand((count, 1), device=device, dtype=torch.float32)
    t = torch.rand((count, 1), device=device, dtype=torch.float32)
    wall_selector = torch.rand((count, 1), device=device, dtype=torch.float32)
    wall_points = torch.cat([torch.where(wall_selector > 0.5, torch.ones_like(x), torch.zeros_like(x)), t], dim=1)
    wall_targets = torch.zeros((count, 1), device=device, dtype=torch.float32)

    initial_x = torch.rand((count, 1), device=device, dtype=torch.float32)
    initial_t = torch.zeros((count, 1), device=device, dtype=torch.float32)
    initial_points = torch.cat([initial_x, initial_t], dim=1)

    if kind == "heat_1d":
        initial_targets = torch.sin(math.pi * initial_x)
    else:
        initial_targets = -torch.sin(math.pi * initial_x)

    points = torch.cat([wall_points, initial_points], dim=0)
    targets = torch.cat([wall_targets, initial_targets], dim=0)
    return points, targets


def _compute_residual_loss(model, points, pde_config: dict):
    import torch

    kind = pde_config.get("kind") or "laplace_2d"
    if kind == "poisson_2d":
        residual = _poisson_residual(model, points, pde_config.get("source_type") or "zero")
    elif kind == "heat_1d":
        residual = _heat_residual(model, points, float(pde_config.get("alpha", 0.1)))
    elif kind == "burgers_1d":
        residual = _burgers_residual(model, points, float(pde_config.get("viscosity", 0.01)))
    else:
        residual = _laplace_residual(model, points)
    return torch.mean(residual.pow(2))


def _compute_boundary_loss(model, points, targets):
    import torch

    predictions = model(points)
    return torch.mean((predictions - targets) ** 2)


def _optimizer_for(model, name: str, learning_rate: float):
    import torch.optim as optim

    key = (name or "adam").lower()
    if key == "sgd":
        return optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9)
    return optim.Adam(model.parameters(), lr=learning_rate)


def train_with_torch(config: dict, progress_callback, cancel_callback):
    import torch

    solver_config = config.get("solver_config") or {}
    network_config = solver_config.get("network") or {}
    pde_config = solver_config.get("pde") or {}

    requested_device = (os.getenv("PINNSOLVER_TORCH_DEVICE") or "auto").lower()
    if requested_device == "cpu":
        device = torch.device("cpu")
    elif requested_device == "cuda" and torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, architecture = build_model(network_config)
    model.to(device)
    model.train()

    optimizer = _optimizer_for(
        model,
        solver_config.get("optimizer") or "adam",
        float(solver_config.get("learning_rate", config.get("learning_rate", 0.001))),
    )

    epochs = max(1, int(config.get("epochs", 1000)))
    n_points = max(16, int(config.get("n_points", 256)))
    n_boundary = max(8, int(config.get("n_boundary", 128)))
    input_dim = int(network_config.get("input_dim") or 2)
    lambda_boundary = float(solver_config.get("lambda_boundary", 10.0))
    batch_size = max(1, int(solver_config.get("collocation_batch_size", min(max(n_points // 2, 16), 128))))
    log_interval = max(1, min(epochs // 50, 20))
    losses = []

    progress_callback(
        progress=0.03,
        mode="python",
        note=f"Training with PyTorch backend ({architecture}) because Rust module is unavailable.",
    )

    for epoch in range(epochs):
        if cancel_callback():
            raise RuntimeError("cancelled")

        collocation_points = _sample_collocation_points(n_points, input_dim, device)
        boundary_points, boundary_targets = _sample_boundary_points(
            pde_config.get("kind") or "laplace_2d",
            n_boundary,
            config,
            device,
        )

        if collocation_points.shape[0] > batch_size:
            indices = torch.randperm(collocation_points.shape[0], device=device)[:batch_size]
            collocation_points = collocation_points[indices]

        collocation_points.requires_grad_(True)
        boundary_points = boundary_points.detach()
        boundary_targets = boundary_targets.detach()

        optimizer.zero_grad(set_to_none=True)
        residual_loss = _compute_residual_loss(model, collocation_points, pde_config)
        boundary_loss = _compute_boundary_loss(model, boundary_points, boundary_targets)
        total_loss = residual_loss + lambda_boundary * boundary_loss
        total_loss.backward()
        optimizer.step()

        loss_value = float(total_loss.detach().cpu().item())
        losses.append(loss_value)

        should_report = epoch == epochs - 1 or epoch % log_interval == 0
        if should_report:
            ratio = (epoch + 1) / epochs
            progress_callback(
                progress=min(0.08 + ratio * 0.84, 0.92),
                losses=list(losses),
                note=(
                    f"PyTorch backend active on {device.type}. "
                    f"Residual loss={float(residual_loss.detach().cpu().item()):.4e}, "
                    f"boundary loss={float(boundary_loss.detach().cpu().item()):.4e}"
                ),
            )

    solution = predict_solution(model, config, device)
    return {
        "losses": losses,
        "solution": solution,
        "device": device.type,
        "architecture": architecture,
    }


def predict_solution(model, config: dict, device):
    import torch

    model.eval()
    kind = ((config.get("solver_config") or {}).get("pde") or {}).get("kind") or "laplace_2d"
    x = np.linspace(0, 1, 50, dtype=np.float32)
    y = np.linspace(0, 1, 50, dtype=np.float32)
    grid_x, grid_y = np.meshgrid(x, y)
    points = np.column_stack([grid_x.ravel(), grid_y.ravel()])

    with torch.no_grad():
        tensor_points = torch.tensor(points, device=device, dtype=torch.float32)
        values = model(tensor_points).detach().cpu().numpy().reshape(50, 50)

    axis_labels = {
        "laplace_2d": ("x", "y"),
        "poisson_2d": ("x", "y"),
        "heat_1d": ("x", "t"),
        "burgers_1d": ("x", "t"),
    }

    return {
        "x": x.tolist(),
        "y": y.tolist(),
        "u": values.tolist(),
        "axes": list(axis_labels.get(kind, ("x", "y"))),
    }
