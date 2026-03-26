from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import problems_router, results_router, system_router, training_router
from data.models import init_db
from tasks.celery_app import ensure_runtime_dirs

init_db()
ensure_runtime_dirs()

app = FastAPI(title="PINN-Solve API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems_router)
app.include_router(training_router)
app.include_router(results_router)
app.include_router(system_router)

@app.get("/")
async def root():
    return {"message": "PINN-Solve API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
