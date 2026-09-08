from typing import Annotated
from fastapi import Depends, Request

from demon_cry.core.module_registry import ModuleRegistry

def get_registry(request: Request) -> ModuleRegistry:
    return request.app.state.registry

AppRegistry = Annotated[ModuleRegistry, Depends(get_registry)]
