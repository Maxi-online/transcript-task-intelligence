from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMProvider(ABC):
    """Абстрактный базовый класс для всех LLM-провайдеров.

    Methods:
        generate(prompt: str) -> str: Генерация ответа на промт.
        agenerate(prompt: str) -> str: Асинхронная генерация ответа на промт.
    """
    def __init__(self, system_message: str):
        """Инициализация базового класса для LLM-провайдеров.

        Args:
            system_message (str): Системная инструкция модели.
        """
        self.model_params: Dict[str, Any] | None = None
        self.system_message = system_message


    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Генерация текста на основе промта.

        Args:
            prompt (str): Входной текст запроса.

        Returns:
            str: Ответ модели.

        Raises:
            NotImplementedError: Если метод не реализован.
        """
        raise NotImplementedError("Метод generate() должен быть переопределен")

    @abstractmethod
    async def agenerate(self, prompt: str) -> str:
        """Асинхронная генерация текста на основе промта.

        Args:
            prompt (str): Входной текст запроса.

        Returns:
            str: Ответ модели.

        Raises:
            NotImplementedError: Если метод не реализован.
        """
        raise NotImplementedError("Метод agenerate() должен быть переопределен")
