from .problems import router as problems_router
from .training import router as training_router
from .results import router as results_router
from .system import router as system_router
from .datasets import router as datasets_router
from .database import router as database_router

__all__ = ["problems_router", "training_router", "results_router", "system_router", "datasets_router", "database_router"]
