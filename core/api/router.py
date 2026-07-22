from fastapi import APIRouter

from core.api import (
    investigate,
    health
)

router = APIRouter(prefix="/api")

router.include_router(health.router, tags=["health"])
router.include_router(investigate.router, tags=["investigation"])
