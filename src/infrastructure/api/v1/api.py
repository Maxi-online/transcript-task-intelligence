from src.infrastructure.api.v1.routers.agents import router as agents_router
from fastapi import APIRouter

router = APIRouter(prefix="/v1")

# Подключение роутеров
router.include_router(agents_router)
