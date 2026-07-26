from fastapi import APIRouter

from app.api.endpoints.apis import router as url_router
from app.api.endpoints.health import router as health_router

router = APIRouter()

router.include_router(
    health_router,
    tags=["Health"]
)

router.include_router(
    url_router,
    tags=["URLs"]
)