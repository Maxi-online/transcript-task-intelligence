from src.config.app_config import settings
from src.core.interfaces import LLMProvider
from openai import OpenAI, AsyncOpenAI
import httpx
import logging
from typing import Optional


class DeepSeekProvider(LLMProvider):
    "It's for DeepSeek LLM API."
    def __init__(self, system_message: str):
        super().__init__(system_message)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_params = settings.deepseek.model_params.model_dump()

        self.async_client = AsyncOpenAI(api_key=settings.deepseek.api_key, base_url=settings.deepseek.base_url)
        self.client = OpenAI(api_key=settings.deepseek.api_key, base_url=settings.deepseek.base_url)

    def _create_messages(self, prompt: str):
        return [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": prompt}
        ]

    def generate(self, prompt: str, **kwargs) -> Optional[str]:
        'Text generation via DeepSeek API.'
        try:
            messages = self._create_messages(prompt)

            completion = self.client.chat.completions.create(
                model=settings.deepseek.model,
                messages=messages,
                temperature=settings.deepseek.temperature,
                max_tokens=settings.deepseek.max_tokens,
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
                model=settings.deepseek.model,
                messages=messages,
                temperature=settings.deepseek.temperature,
                max_tokens=settings.deepseek.max_tokens,
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

        except Exception as e:
            self.logger.error(f"Asynchronous error of generation: {str(e)}")
            raise RuntimeError(f"Asynchronous error of generation: {str(e)}")
