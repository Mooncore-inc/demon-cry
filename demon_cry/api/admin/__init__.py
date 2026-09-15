from fastapi import APIRouter, Depends

from demon_cry.api.admin.llm_models import llm_models_router
from demon_cry.api.admin.plugins import plugins_router
from demon_cry.api.admin.settings import settings_router
from demon_cry.api.admin.users import users_router
from demon_cry.api.dependencies.auth import require_admin

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])
admin_router.include_router(users_router, tags=["Users"])
admin_router.include_router(settings_router, tags=["Settings"])
admin_router.include_router(plugins_router, tags=["Plugins"])
admin_router.include_router(llm_models_router, tags=["LLM Models"])

__all__ = ["admin_router"]
