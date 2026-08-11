from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.fraud import router as fraud_router

router = APIRouter()

router.include_router(health_router, tags=["health"])
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(documents_router)
router.include_router(chat_router)
router.include_router(fraud_router)
