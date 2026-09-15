from typing import Annotated

from fastapi import Depends, Request

from demon_cry.core.plugin_registry import PluginRegistry


def get_registry(request: Request) -> PluginRegistry:
    return request.app.state.registry


AppRegistry = Annotated[PluginRegistry, Depends(get_registry)]
