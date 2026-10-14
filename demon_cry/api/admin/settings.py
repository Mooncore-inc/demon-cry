from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import UoWDep
from demon_cry.api.schemas.settings import SettingResponse, SettingUpdate

settings_router = APIRouter(prefix="/settings")


@settings_router.get("/", response_model=list[SettingResponse])
async def get_all_settings(uow: UoWDep):
    settings = await uow.settings.get_all()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@settings_router.get("/{key}", response_model=SettingResponse)
async def get_settings(key: str, uow: UoWDep):
    settings = await uow.settings.get(key=key)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@settings_router.patch("/{key}", response_model=SettingResponse)
async def update_settings(key: str, body: SettingUpdate, uow: UoWDep):
    settings = await uow.settings.get(key=key)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    async with uow.transaction():
        return await uow.settings.update(
            settings, **body.model_dump(exclude_unset=True)
        )
