from fastapi import APIRouter

from .generation_routes import router as generation_router
from .save_mutation_routes import router as save_mutation_router
from .save_query_routes import router as save_query_router
from .segment_routes import router as segment_router
from .session_routes import router as session_router

router = APIRouter()
router.include_router(generation_router)
router.include_router(session_router)
router.include_router(segment_router)
router.include_router(save_query_router)
router.include_router(save_mutation_router)
