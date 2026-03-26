from .problems import router as problems_router
from .training import router as training_router
from .results import router as results_router

__all__ = ["problems_router", "training_router", "results_router"]
