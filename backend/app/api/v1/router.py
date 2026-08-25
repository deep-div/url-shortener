from fastapi import APIRouter

from app.api.v1.endpoints.apis import router as url_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.sse import router as sse_router

router = APIRouter()

router.include_router(health_router, tags=["Health"])
router.include_router(url_router, tags=["URLs"])
router.include_router(sse_router, tags=["SSE"])