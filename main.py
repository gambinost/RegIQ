from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import base_router as health_router
from api.routes.hitl import router as hitl_router
from core.settings import get_settings
from rich.console import Console

console = Console()
settings = get_settings()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(health_router)
app.include_router(hitl_router)

# CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD
    )
