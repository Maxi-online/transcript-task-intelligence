from fastapi import FastAPI
from src.infrastructure.api.v1.api import router as v1_router
from src.infrastructure.api.v1.dependencies import get_llm_monitoring
from src.config.app_config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    import src.config.logging_config
    yield

    print("Завершение работы приложения ...")
    # Выполнение кода после завершения приложения
    if settings.langfuse.enabled and get_llm_monitoring.cache_info().currsize:
        try:
            get_llm_monitoring().flush()
            print("Данные успешно загружены в Langfuse UI.")
        except Exception as e:
            print(f"Ошибка при загрузке данных в Langfuse UI: {e}")


# Определение fastapi app и routers
app = FastAPI(lifespan=lifespan)
app.include_router(v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
