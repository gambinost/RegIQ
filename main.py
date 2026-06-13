from fastapi import FastAPI
from api.routes.health import base_router as health_router
from core.settings import get_settings
from rich.console import Console

console = Console()
settings = get_settings()


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD
    )
