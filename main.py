from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routes.health import base_router as health_router
from api.routes.hitl import router as hitl_router
from api.routes.regulations import router as regulations_router
from core.settings import get_settings
from rich.console import Console

console = Console()
settings = get_settings()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(health_router)
app.include_router(hitl_router)
app.include_router(regulations_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React frontend (must be after API routes)
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD
    )
