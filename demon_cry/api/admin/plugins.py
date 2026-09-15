from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import PluginRepo
from demon_cry.api.schemas.plugins import PluginResponse, PluginUpdate

plugins_router = APIRouter(prefix="/plugins")


@plugins_router.get("/", response_model=list[PluginResponse])
async def get_all_plugins(plugin_repo: PluginRepo):
    return await plugin_repo.get_all()


@plugins_router.get("/{plugin_name}", response_model=PluginResponse)
async def get_plugin(plugin_name: str, plugin_repo: PluginRepo):
    plugin = await plugin_repo.get(plugin_name=plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@plugins_router.patch("/{plugin_name}", response_model=PluginResponse)
async def update_plugin(plugin_name: str, body: PluginUpdate, plugin_repo: PluginRepo):
    plugin = await plugin_repo.get(plugin_name=plugin_name)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return await plugin_repo.update(plugin, **body.model_dump(exclude_unset=True))
