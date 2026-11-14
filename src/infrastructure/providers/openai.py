import logging
import asyncio
from typing import Optional

import httpx
from openai import OpenAI, AsyncOpenAI

from src.config.app_config import settings
from src.core.interfaces import LLMProvider


class OpenAIProvider(LLMProvider):
    'OpenAI API.'
    def __init__(self, system_message: str):
        super().__init__(system_message)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_params = settings.openai.model_params.model_dump()

        # -------------------------------------------------------------------------------------------
        self.proxy_url: str | None = settings.openai.proxy_url

        # Synchronous httpx client
        sync_http_client: httpx.Client | None = None
        if self.proxy_url:
            sync_http_client = httpx.Client(
                transport=httpx.HTTPTransport(proxy=self.proxy_url),
                timeout=60.0,
            )

        # Asynchronous httpx client
        async_http_client: httpx.AsyncClient | None = None
        if self.proxy_url:
            async_http_client = httpx.AsyncClient(
                transport=httpx.AsyncHTTPTransport(proxy=self.proxy_url),
                timeout=60.0,
            )

        # ----- OpenAI SDK clients -----
        base_url = settings.openai.base_url or "https://api.openai.com/v1"
        # Error: Remove the wrong sufix if it is
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
        'Text generation via OpenAI API.'
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
                error_message = 'The API returned an empty array of choices.'
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.choices[0].message.content

        except httpx.HTTPStatusError as e:
            error_message = f"Error in Appeal: {e.response.status_code}"
            self.logger.error(error_message)
            raise ConnectionError(error_message)

        except httpx.TimeoutException:
            error_message = 'API Request Timeout'
            self.logger.warning(error_message)
            raise TimeoutError(error_message)

        except Exception as e:
            self.logger.error(f"Error of Generation: {str(e)}")
            raise RuntimeError(f"Error of Generation: {str(e)}")

    async def agenerate(self, prompt: str, **kwargs) -> Optional[str]:
        'Asynchronous text generation.'
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
                error_message = 'API returned the empty choices.'
                self.logger.error(error_message)
                raise ValueError(error_message)

            return completion.choices[0].message.content

        except httpx.HTTPStatusError as e:
            error_message = f"Asynchronous request for API errors: {e.response.status_code}"
            self.logger.error(error_message)
            raise ConnectionError(error_message)

        except asyncio.TimeoutError:
            error_message = 'API Asynchronous Request Time'
            self.logger.warning(error_message)
            raise TimeoutError(error_message)

        except Exception as e:
            self.logger.error(f"Asynchronous error of generation: {str(e)}")
            raise RuntimeError(f"Asynchronous error of generation: {str(e)}")
