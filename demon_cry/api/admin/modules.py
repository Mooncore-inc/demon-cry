from fastapi import APIRouter, HTTPException

from demon_cry.api.dependencies import ModuleRepo
from demon_cry.api.schemas.modules import ModuleResponse, ModuleUpdate

modules_router = APIRouter(prefix="/modules")


@modules_router.get("/", response_model=list[ModuleResponse])
async def get_all_modules(module_repo: ModuleRepo):
    return await module_repo.get_all()


@modules_router.get("/{module_name}", response_model=ModuleResponse)
async def get_module(module_name: str, module_repo: ModuleRepo):
    module = await module_repo.get(module_name=module_name)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


@modules_router.patch("/{module_name}", response_model=ModuleResponse)
async def update_module(module_name: str, body: ModuleUpdate, module_repo: ModuleRepo):
    module = await module_repo.get(module_name=module_name)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return await module_repo.update(module, **body.model_dump(exclude_unset=True))
