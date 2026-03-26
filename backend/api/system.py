from fastapi import APIRouter

from services.system_status import list_workers, queue_overview

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/workers")
async def get_workers():
    return {
        "items": list_workers(),
    }


@router.get("/queue")
async def get_queue():
    return queue_overview()


@router.get("/overview")
async def get_overview():
    workers = list_workers()
    queue = queue_overview()
    return {
        "workers": workers,
        "queue": queue,
    }
