from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/problems", tags=["problems"])

class ProblemConfig(BaseModel):
    name: str
    pde: str
    domain: dict
    boundary_conditions: list = []

problems_db = {}

@router.post("/")
async def create_problem(problem: ProblemConfig):
    problem_id = f"prob-{len(problems_db) + 1}"
    problems_db[problem_id] = problem.dict()
    return {"id": problem_id, "status": "created"}

@router.get("/{problem_id}")
async def get_problem(problem_id: str):
    if problem_id not in problems_db:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"id": problem_id, **problems_db[problem_id]}
