from fastapi import APIRouter, Depends
from demon_cry.api.auth import require_admin

from demon_cry.api.admin.users import users_router

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])
admin_router.include_router(users_router)

__all__ = ["admin_router"]
