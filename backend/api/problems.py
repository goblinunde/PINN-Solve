from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/problems", tags=["problems"])


class ProblemConfig(BaseModel):
    name: str
    pde: str
    domain: dict
    boundary_conditions: list = []


problems_db = {}

CATALOG = {
    "pde_presets": [
        {
            "key": "laplace_2d",
            "name": "2D Laplace",
            "description": "Steady-state elliptic equation on the unit square.",
            "display_equation": "u_xx + u_yy = 0",
            "input_dim": 2,
            "defaults": {"source_type": "zero", "alpha": 0.1, "viscosity": 0.01},
        },
        {
            "key": "poisson_2d",
            "name": "2D Poisson",
            "description": "Elliptic equation with configurable source term.",
            "display_equation": "u_xx + u_yy = f(x, y)",
            "input_dim": 2,
            "defaults": {"source_type": "sine", "alpha": 0.1, "viscosity": 0.01},
        },
        {
            "key": "heat_1d",
            "name": "1D Heat",
            "description": "Transient diffusion in x-t space with zero boundary walls.",
            "display_equation": "u_t - alpha * u_xx = 0",
            "input_dim": 2,
            "defaults": {"source_type": "zero", "alpha": 0.1, "viscosity": 0.01},
        },
        {
            "key": "burgers_1d",
            "name": "1D Burgers",
            "description": "Nonlinear transport-diffusion benchmark in x-t space.",
            "display_equation": "u_t + u u_x - nu * u_xx = 0",
            "input_dim": 2,
            "defaults": {"source_type": "zero", "alpha": 0.1, "viscosity": 0.01},
        },
    ],
    "optimizers": [
        {"key": "adam", "name": "Adam", "description": "Good default for mixed PINN losses."},
        {"key": "sgd", "name": "SGD", "description": "Simpler optimizer for stable manual tuning."},
    ],
    "activations": [
        {"key": "tanh", "name": "Tanh"},
        {"key": "relu", "name": "ReLU"},
        {"key": "sigmoid", "name": "Sigmoid"},
        {"key": "softplus", "name": "Softplus"},
        {"key": "linear", "name": "Linear"},
    ],
    "source_types": [
        {"key": "zero", "name": "Zero"},
        {"key": "one", "name": "Constant One"},
        {"key": "sine", "name": "Sine Source"},
    ],
    "output_activations": [
        {"key": "linear", "name": "Linear"},
        {"key": "tanh", "name": "Tanh"},
        {"key": "sigmoid", "name": "Sigmoid"},
    ],
    "network_presets": [
        {
            "key": "baseline",
            "name": "Baseline",
            "description": "Two tanh blocks, balanced for most PDE demos.",
            "hidden_layers": [
                {"size": 32, "activation": "tanh", "residual": False},
                {"size": 32, "activation": "tanh", "residual": False},
            ],
        },
        {
            "key": "wide",
            "name": "Wide",
            "description": "More neurons per block to improve representation power.",
            "hidden_layers": [
                {"size": 64, "activation": "tanh", "residual": False},
                {"size": 64, "activation": "tanh", "residual": False},
            ],
        },
        {
            "key": "deep",
            "name": "Deep",
            "description": "Four hidden layers for richer function spaces.",
            "hidden_layers": [
                {"size": 32, "activation": "tanh", "residual": False},
                {"size": 32, "activation": "tanh", "residual": False},
                {"size": 32, "activation": "tanh", "residual": False},
                {"size": 32, "activation": "tanh", "residual": False},
            ],
        },
        {
            "key": "residual",
            "name": "Residual",
            "description": "Residual tanh blocks to stabilize deeper training.",
            "hidden_layers": [
                {"size": 48, "activation": "tanh", "residual": False},
                {"size": 48, "activation": "tanh", "residual": True},
                {"size": 48, "activation": "tanh", "residual": True},
            ],
        },
    ],
}


@router.get("/catalog")
async def get_problem_catalog():
    return CATALOG

@router.post("/")
async def create_problem(problem: ProblemConfig):
    problem_id = f"prob-{len(problems_db) + 1}"
    problems_db[problem_id] = problem.model_dump()
    return {"id": problem_id, "status": "created"}


@router.get("/{problem_id}")
async def get_problem(problem_id: str):
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"id": problem_id, **problems_db[problem_id]}
