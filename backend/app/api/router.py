from fastapi import APIRouter

from app.api.endpoints.apis import router as url_router

router = APIRouter()
router.include_router(url_router)
