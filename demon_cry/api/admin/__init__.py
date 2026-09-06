from fastapi import APIRouter, Depends
from demon_cry.api.dependencies.auth import require_admin

from demon_cry.api.admin.users import users_router
from demon_cry.api.admin.settings import settings_router

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])
admin_router.include_router(users_router, tags=["Users"])
admin_router.include_router(settings_router, tags=["Settings"])

__all__ = ["admin_router"]
