from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import UoWDep
from demon_cry.api.schemas.plugins import PluginResponse, PluginUpdate

plugins_router = APIRouter(prefix="/plugins")


@plugins_router.get("/", response_model=list[PluginResponse])
async def get_all_plugins(uow: UoWDep):
    return await uow.plugins.get_all()


@plugins_router.get("/{plugin_name}", response_model=PluginResponse)
async def get_plugin(plugin_name: str, uow: UoWDep):
    plugin = await uow.plugins.get(plugin_name=plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@plugins_router.patch("/{plugin_name}", response_model=PluginResponse)
async def update_plugin(plugin_name: str, body: PluginUpdate, uow: UoWDep):
    plugin = await uow.plugins.get(plugin_name=plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    async with uow.transaction():
        return await uow.plugins.update(plugin, **body.model_dump(exclude_unset=True))
