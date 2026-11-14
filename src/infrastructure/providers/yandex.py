from src.config.app_config import settings
from src.core.interfaces import LLMProvider
from yandex_cloud_ml_sdk import YCloudML
from concurrent.futures import ThreadPoolExecutor
import asyncio
import logging


class YandexProvider(LLMProvider):
    "It's for Yandex LLM API."
    def __init__(self, system_message: str):
        super().__init__(system_message)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_params = settings.yandex.model_params.model_dump()

        self.client = YCloudML(folder_id=settings.yandex.folder, auth=settings.yandex.api_key)

        # To handle asynchronous requests
        self.executor = ThreadPoolExecutor(max_workers=10)

    def _create_messages(self, prompt: str):
        return [
            {"role": "system", "text": self.system_message},
            {"role": "user", "text": prompt}
        ]

    def generate(self, prompt: str, **kwargs) -> str:
        'Text generation via Yandex API.'
        try:
            messages = self._create_messages(prompt)

            completion = self.client.models.completions(settings.yandex.model).configure(
                temperature=settings.yandex.temperature,
                max_tokens=settings.yandex.max_tokens,
                **kwargs
            ).run(messages=messages)

            if not completion.alternatives:
                error_message = 'The API returned an empty array of algorithms.'
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.alternatives[0].text

        except Exception as e:
            self.logger.error(f"Error of Generation: {str(e)}")
            raise RuntimeError(f"Error of Generation: {str(e)}")

    async def agenerate(self, prompt: str, **kwargs) -> str:
        'Asynchronous text generation via Yandex API.'
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
                error_message = 'API returned an empty array of algorithms).'
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.alternatives[0].text

        except Exception as e:
            self.logger.error(f"Asynchronous error of generation: {str(e)}")
            raise RuntimeError(f"Asynchronous error of generation: {str(e)}")
