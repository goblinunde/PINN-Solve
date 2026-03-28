from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from services.datasets import create_dataset, get_dataset_detail, list_datasets

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


class DatasetImportRequest(BaseModel):
    name: str = "Training Dataset"
    pde_kind: str = "generic"
    description: str | None = None
    inputs: list[list[float]] = Field(default_factory=list)
    targets: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_lengths(self):
        if self.targets and len(self.targets) != len(self.inputs):
            raise ValueError("targets length must match inputs length")
        return self


@router.post("/import")
async def import_dataset(payload: DatasetImportRequest):
    if not payload.inputs:
        raise HTTPException(status_code=400, detail="inputs cannot be empty")
    return create_dataset(payload.model_dump())


@router.get("/")
async def get_datasets():
    items = list_datasets()
    return {
        "items": items,
        "total": len(items),
    }


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    dataset = get_dataset_detail(dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset
