from fastapi import APIRouter
from fastapi.params import Depends

from configs.config import Settings, get_settings

base_router = APIRouter(prefix="/api/v1", tags=["api_v1", "health"])


@base_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RegIQ", "message": "RegIQ is up and running!"}


@base_router.get("/info")
async def get_info(app_settings: Settings = Depends(get_settings)):
    return {"app_name": app_settings.app_name, "app_version": app_settings.app_version}
