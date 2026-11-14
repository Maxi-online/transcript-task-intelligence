from typing import Dict, Optional, Any, List
from langfuse import Langfuse
from src.core.interfaces import LLMMonitoringProvider
from src.config.app_config import settings


class LangfuseProvider(LLMMonitoringProvider):
    def __init__(self):
        self._langfuse = Langfuse(
            enabled=settings.langfuse.enabled,
            public_key=settings.langfuse.public_key,
            secret_key=settings.langfuse.secret_key,
            host=settings.langfuse.host,
            flush_interval=settings.langfuse.flush_interval,
        )

    def trace(
        self,
        name: str,
        user_id: str,
        input: Optional[Dict] = None,
        output: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ):
        trace = self._langfuse.trace(
            name=name,
            user_id=user_id,
            input=input,
            output=output,
            metadata=metadata,
            tags=tags
        )

        return trace

    def update_trace(self, trace = None, output: Optional[Dict] = None, **kwargs):
        trace.update(output=output, **kwargs)

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
        # Development of metadata for Langfuse transmission
        metadata_values = {}
        if model_parameters:
            metadata_values["model_parameters"] = model_parameters
        if level:
            metadata_values["level"] = level
        if status_message:
            metadata_values["status"] = status_message
        if metadata:
            metadata_values.update(metadata)

        span = self._langfuse.span(
            name=name,
            trace_id=trace_id,
            parent_observation_id=parent_observation_id,
            input=input,
            output=output,
            metadata=metadata_values,
            **kwargs
        )

        return span

    def update_span(self, span = None, output: Optional[Dict] = None, **kwargs):
        span.update(output=output, **kwargs)

    def end_span(self, span: Optional[Any] = None, output: Optional[Dict] = None):
        span.end(output=output)

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
        # Development of metadata for Langfuse transmission
        metadata_values = {}
        if level:
            metadata_values["level"] = level
        if status_message:
            metadata_values["status"] = status_message
        if metadata:
            metadata_values.update(metadata)

        generation = self._langfuse.generation(
            name=name,
            trace_id=trace_id,
            parent_observation_id=parent_observation_id,
            input=input,
            output=output,
            model=model,
            model_parameters=model_parameters,
            metadata=metadata_values,
            usage=usage_details,
            **kwargs
        )

        return generation

    def update_generation(self, generation = None, output: Optional[Dict] = None, **kwargs):
        generation.update(output=output, **kwargs)

    def end_generation(self, generation: Optional[Any] = None, output: Optional[Dict] = None):
        generation.end(output=output)

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
        # Development of metadata for Langfuse transmission
        metadata_values = {}
        if level:
            metadata_values["level"] = level
        if status_message:
            metadata_values["status"] = status_message
        if metadata:
            metadata_values.update(metadata)

        event = self._langfuse.event(
            name=name,
            trace_id=trace_id,
            parent_observation_id=parent_observation_id,
            input=input,
            output=output,
            metadata=metadata_values,
            **kwargs
        )

        return event

    def update_event(self, event = None, output: Optional[Dict] = None, **kwargs):
        event.update(output=output, **kwargs)

    def end_event(self, event: Optional[Any] = None, output: Optional[Dict] = None):
        event.end(output=output)

    def score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: Optional[str] = None,
        observation_id: Optional[str] = None
    ):
        self._langfuse.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
            observation_id=observation_id
        )

    def flush(self):
        self._langfuse.flush()
