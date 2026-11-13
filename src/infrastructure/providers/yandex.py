from src.config.app_config import settings
from src.core.interfaces import LLMProvider
from yandex_cloud_ml_sdk import YCloudML
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging


class YandexProvider(LLMProvider):
    """Провайдер для Yandex LLM API."""
    def __init__(self, system_message: str):
        super().__init__(system_message)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_params = settings.yandex.model_params.model_dump()

        self.client = YCloudML(folder_id=settings.yandex.folder, auth=settings.yandex.api_key)

        # Для обработки асинхронных запросов
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _create_messages(self, prompt: str):
        return [
            {"role": "system", "text": self.system_message},
            {"role": "user", "text": prompt}
        ]

    def generate(self, prompt: str, **kwargs) -> str:
        """Генерация текста через Yandex API."""
        try:
            messages = self._create_messages(prompt)

            completion = self.client.models.completions(settings.yandex.model).configure(
                temperature=settings.yandex.temperature,
                max_tokens=settings.yandex.max_tokens,
                **kwargs
            ).run(messages=messages)

            if not completion.alternatives:
                error_message = "API вернуло пустой массив alternatives."
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.alternatives[0].text

        except Exception as e:
            self.logger.error(f"Ошибка генерации: {str(e)}")
            raise RuntimeError(f"Ошибка генерации: {str(e)}")

    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Асинхронная генерация текста через Yandex API."""
        try:
            messages = self._create_messages(prompt)

            loop = asyncio.get_event_loop()
            func = self.client.models.completions(settings.yandex.model).configure(
                temperature=settings.yandex.temperature,
                max_tokens=settings.yandex.max_tokens,
                **kwargs
            )
            completion = await loop.run_in_executor(self.executor, func.run, messages)

            if not completion.alternatives:
                error_message = "API вернуло пустой массив alternatives (асинхронный вызов)."
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.alternatives[0].text

        except Exception as e:
            self.logger.error(f"Асинхронная ошибка генерации: {str(e)}")
            raise RuntimeError(f"Асинхронная ошибка генерации: {str(e)}")
