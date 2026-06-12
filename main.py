from fastapi import FastAPI
from api.routes.health import base_router as health_router
from configs.config import get_settings
from rich.console import Console

console = Console()
settings = get_settings()


app = FastAPI(title="RegIQ API", version=settings.app_version)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host=settings.api_host, port=settings.api_port, reload=settings.api_reload
    )
