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
        'Creates a new trade and returns it to ID.'
        pass

    @abstractmethod
    def update_trace(self, trace = None, output: Optional[Dict] = None, **kwargs):
        'Updates data for existing trade.'
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
        'Creates a new span inside trade and returns it to ID.'
        pass

    @abstractmethod
    def update_span(self, span = None, output: Optional[Dict] = None, **kwargs):
        'Updates data for existing span.'
        pass

    @abstractmethod
    def end_span(self, span: Optional[Any] = None, output: Optional[Dict] = None):
        'Ends span.'
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
        'Creates a new energy within the trade.'
        pass

    @abstractmethod
    def update_generation(self, generation = None, output: Optional[Dict] = None, **kwargs):
        'Updates data for existing energy.'
        pass

    @abstractmethod
    def end_generation(self, generation: Optional[Any] = None, output: Optional[Dict] = None):
        'Completes the generation.'
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
        'Creates a new event inside trade.'
        pass

    @abstractmethod
    def update_event(self, event: Optional[Any] = None, output: Optional[Dict] = None, **kwargs):
        'Updates data for existing event.'
        pass

    @abstractmethod
    def end_event(self, event: Optional[Any] = None, output: Optional[Dict] = None):
        'Ends the event.'
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
        'Adds the "score" to "trace".'
        pass

    @abstractmethod
    def flush(self):
        'Sends all stored data to the server.'
        pass
