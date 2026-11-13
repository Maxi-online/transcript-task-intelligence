from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMMonitoringProvider(ABC):
    @abstractmethod
    def trace(
        self,
        name: str,
        user_id: str,
        input: Optional[Dict] = None,
        output: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[list] = None
    ):
        """Создает новый trace (трассировку) и возвращает его ID."""
        pass

    @abstractmethod
    def update_trace(self, trace = None, output: Optional[Dict] = None, **kwargs):
        """Обновляет данные для существующего trace."""
        pass

    @abstractmethod
    def span(
        self,
        name: str,
        trace_id: str,
        model: Optional[str] = None,
        parent_observation_id: Optional[str] = None,
        model_parameters: Optional[Dict[str, Any]] = None,
        input: Optional[Dict] = None,
        output: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        level: Optional[str] = None,
        status_message: Optional[str] = None,
        **kwargs
    ):
        """Создает новый span (промежуток) внутри trace и возвращает его ID."""
        pass

    @abstractmethod
    def update_span(self, span = None, output: Optional[Dict] = None, **kwargs):
        """Обновляет данные для существующего span."""
        pass

    @abstractmethod
    def end_span(self, span: Optional[Any] = None, output: Optional[Dict] = None):
        """Завершает span."""
        pass

    @abstractmethod
    def generation(
        self,
        name: str,
        trace_id: str,
        model: str,
        parent_observation_id: Optional[str] = None,
        input: Optional[Dict] = None,
        output: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        level: Optional[str] = None,
        status_message: Optional[str] = None,
        usage_details: Optional[Dict] = None,
        **kwargs
    ):
        """Создает новый generation внутри trace."""
        pass

    @abstractmethod
    def update_generation(self, generation = None, output: Optional[Dict] = None, **kwargs):
        """Обновляет данные для существующего generation."""
        pass

    @abstractmethod
    def end_generation(self, generation: Optional[Any] = None, output: Optional[Dict] = None):
        """Завершает generation."""
        pass

    @abstractmethod
    def event(
        self,
        name: str,
        trace_id: str,
        parent_observation_id: Optional[str] = None,
        input: Optional[Dict] = None,
        output: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        level: Optional[str] = None,
        status_message: Optional[str] = None,
        **kwargs
    ):
        """Создает новый event внутри trace."""
        pass

    @abstractmethod
    def update_event(self, event: Optional[Any] = None, output: Optional[Dict] = None, **kwargs):
        """Обновляет данные для существующего event."""
        pass

    @abstractmethod
    def end_event(self, event: Optional[Any] = None, output: Optional[Dict] = None):
        """Завершает event."""
        pass

    @abstractmethod
    def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
        observation_id: Optional[str] = None
    ):
        """Добавляет оценку (score) к trace."""
        pass

    @abstractmethod
    def flush(self):
        """Отправляет все накопленные данные на сервер."""
        pass
