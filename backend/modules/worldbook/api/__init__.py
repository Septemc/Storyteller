from fastapi import APIRouter

from .delete_routes import router as delete_router
from .import_routes import router as import_router
from .query_routes import router as query_router

router = APIRouter()
router.include_router(import_router)
router.include_router(query_router)
router.include_router(delete_router)
