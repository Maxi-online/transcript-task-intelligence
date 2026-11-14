from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMProvider(ABC):
    """An abstract basic class for all LLM providers.

    Methods:
        Generate(prompt: str) -> stre: Response generation for promt.
        agenerate(prompt: STR) ->str: Asynchronous response generation.
    """
    def __init__(self, system_message: str):
        """Basic Class Initialization for LLM Providers.

        Args:
            system_message (str): Model system instruction.
        """
        self.model_params: Dict[str, Any] | None = None
        self.system_message = system_message


    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Text generation based on prom.

        Args:
            prompt (str): Input text of the request.

        Returns:
            str: Model response.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError('The method of generality() shall be redefined')

    @abstractmethod
    async def agenerate(self, prompt: str) -> str:
        """Asynchronous text generation based on prom.

        Args:
            prompt (str): Input text of the request.

        Returns:
            str: Model response.

        Raises:
            NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError('The agenerate() method shall be redefined')
