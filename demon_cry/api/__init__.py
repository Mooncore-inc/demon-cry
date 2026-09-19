from fastapi import APIRouter

from demon_cry.api import investigate
from demon_cry.api.admin import admin_router

router = APIRouter(prefix="/api/v1")

router.include_router(investigate.router, tags=["Investigation"])

router.include_router(admin_router)
