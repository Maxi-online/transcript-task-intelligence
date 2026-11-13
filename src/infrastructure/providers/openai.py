import logging
import asyncio
from typing import Optional

import httpx
from openai import OpenAI, AsyncOpenAI

from src.config.app_config import settings
from src.core.interfaces import LLMProvider


class OpenAIProvider(LLMProvider):
    """Провайдер для OpenAI API."""
    def __init__(self, system_message: str):
        super().__init__(system_message)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_params = settings.openai.model_params.model_dump()

        # ----- Настройка прокси -----
        self.proxy_url: str | None = settings.openai.proxy_url

        # Cинхронный httpx клиент
        sync_http_client: httpx.Client | None = None
        if self.proxy_url:
            sync_http_client = httpx.Client(
                transport=httpx.HTTPTransport(proxy=self.proxy_url),
                timeout=60.0,
            )

        # Асинхронный httpx клиент
        async_http_client: httpx.AsyncClient | None = None
        if self.proxy_url:
            async_http_client = httpx.AsyncClient(
                transport=httpx.AsyncHTTPTransport(proxy=self.proxy_url),
                timeout=60.0,
            )

        # ----- OpenAI SDK клиенты -----
        base_url = settings.openai.base_url or "https://api.openai.com/v1"
        # Удаляем ошибочный суффикс, если он есть
        if base_url.rstrip("/").endswith("chat/completions"):
            base_url = base_url.rsplit("/chat/completions", 1)[0]

        self.logger.info(f"OpenAI base_url: {base_url}; proxy: {self.proxy_url}")

        self.sync_client = OpenAI(
            api_key=settings.openai.api_key,
            base_url=base_url,
            http_client=sync_http_client,
        )

        self.async_client = AsyncOpenAI(
            api_key=settings.openai.api_key,
            base_url=base_url,
            http_client=async_http_client,
        )


    def _create_messages(self, prompt: str):
        return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt}
        ]

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        """Генерация текста через OpenAI API."""
        try:
            messages = self._create_messages(prompt)

            completion = self.sync_client.chat.completions.create(
                model=settings.openai.model,
                messages=messages,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
                **kwargs
            )

            if not completion.choices:
                error_message = "API вернуло пустой массив choices."
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.choices[0].message.content

        except httpx.HTTPStatusError as e:
            error_message = f"Ошибка запроса к API: {e.response.status_code}"
            self.logger.error(error_message)
            raise ConnectionError(error_message)

        except httpx.TimeoutException:
            error_message = "Таймаут запроса к API"
            self.logger.warning(error_message)
            raise TimeoutError(error_message)

        except Exception as e:
            self.logger.error(f"Ошибка генерации: {str(e)}")
            raise RuntimeError(f"Ошибка генерации: {str(e)}")

    async def agenerate(self, prompt: str, **kwargs) -> Optional[str]:
        """Асинхронная генерация текста."""
        try:
            messages = self._create_messages(prompt)

            completion = await self.async_client.chat.completions.create(
                model=settings.openai.model,
                messages=messages,
                temperature=settings.openai.temperature,
                max_tokens=settings.openai.max_tokens,
                **kwargs
            )

            if not completion.choices:
                error_message = "API вернуло пустой массив choices (асинхронный вызов)"
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.choices[0].message.content

        except httpx.HTTPStatusError as e:
            error_message = f"Ошибка асинхронного запроса к API: {e.response.status_code}"
            self.logger.error(error_message)
            raise ConnectionError(error_message)

        except asyncio.TimeoutError:
            error_message = "Таймаут асинхронного запроса к API"
            self.logger.warning(error_message)
            raise TimeoutError(error_message)

        except Exception as e:
            self.logger.error(f"Асинхронная ошибка генерации: {str(e)}")
            raise RuntimeError(f"Асинхронная ошибка генерации: {str(e)}")
