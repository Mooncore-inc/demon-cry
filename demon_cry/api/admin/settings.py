from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import SettingsRepo
from demon_cry.api.schemas.settings import SettingResponse, SettingUpdate

settings_router = APIRouter(prefix="/settings")


@settings_router.get("/", response_model=list[SettingResponse])
async def get_all_settings(set_repo: SettingsRepo):
    settings = await set_repo.get_all()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@settings_router.get("/{key}", response_model=SettingResponse)
async def get_settings(key: str, set_repo: SettingsRepo):
    settings = await set_repo.get(key=key)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@settings_router.patch("/{key}", response_model=SettingResponse)
async def update_settings(key: str, body: SettingUpdate, set_repo: SettingsRepo):
    settings = await set_repo.get(key=key)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return await set_repo.update(settings, **body.model_dump(exclude_unset=True))
