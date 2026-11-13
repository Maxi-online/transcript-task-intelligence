from src.core.interfaces import LLMProvider, LLMMonitoringProvider
from typing import Dict
from pydantic import BaseModel


# DTO
class SummarizationDTO(BaseModel):
    user_id: str
    text: str
    tasks: list[str]


class SummarizationAgentDeprecated:
    def __init__(self, providers: Dict[str, LLMProvider], provider_type: str = "yandex"):
        self.providers = providers
        self.provider_type = provider_type

    async def execute(self, text: str, query: str) -> str:
        prompt = f"TEXT: {text}\nQUERY: {query}"

        # Логика выбора провайдера
        if self.provider_type == "yandex":
            provider = self.providers.get("yandex")
        elif self.provider_type == "deepseek":
            provider = self.providers.get("deepseek")
        else:
            raise ValueError("Провайдер не найден")

        return await provider.agenerate(prompt)


class ProvidersUnavailableError(RuntimeError):
    """Every configured provider failed to complete the requested tasks."""


class SummarizationAgent:
    def __init__(self, llm_monitoring: LLMMonitoringProvider, providers: Dict[str, LLMProvider]):
        self.llm_monitoring = llm_monitoring
        self.providers = providers
        self.system_message = None

    def _execute_generation_with_provider(self, task_idx, provider, provider_name, prompt, task_text, trace_id, parent_id):
        params = provider.model_params or {}
        generation = self.llm_monitoring.generation(
            name=f"task-{task_idx}", trace_id=trace_id, model=provider_name,
            parent_observation_id=parent_id, input={"task_text": task_text},
            model_parameters={"temperature": params.get("temperature"), "max_tokens": params.get("max_tokens")},
        )
        try:
            result = provider.generate(prompt)
            self.llm_monitoring.update_generation(generation, output={"answer": result})
            return result
        except Exception as error:
            self.llm_monitoring.update_generation(generation, output={"error_type": type(error).__name__})
            raise
        finally:
            self.llm_monitoring.end_generation(generation)

    def execute(self, input_data: SummarizationDTO) -> str:
        if not input_data.tasks:
            raise ValueError("At least one analysis task is required")
        if not self.providers:
            raise ProvidersUnavailableError("No providers are configured")
        trace = self.llm_monitoring.trace(name="summarization-pipeline", user_id=input_data.user_id,
                                          input=input_data.model_dump(exclude={"user_id"}))
        span = self.llm_monitoring.span(name="tasks-processing", trace_id=trace.id, parent_observation_id=trace.id)
        answers, failures = [], 0
        try:
            for index, task in enumerate(input_data.tasks, 1):
                for name, provider in self.providers.items():
                    try:
                        if self.system_message is None:
                            self.system_message = provider.system_message
                        answer = self._execute_generation_with_provider(index, provider, name,
                            f"TEXT: {input_data.text}\nTASK: {task}\n", task, trace.id, span.id)
                    except Exception:
                        continue
                    answers.append(answer)
                    break
                else:
                    answers.append("Ошибка выполнения задачи")
                    failures += 1
            if failures == len(input_data.tasks):
                self.llm_monitoring.update_trace(trace, output={"error": "all_providers_unavailable"})
                raise ProvidersUnavailableError("All providers are unavailable")
            result = "Получены задачи:" + "".join(f"\n{i}. {task}" for i, task in enumerate(input_data.tasks, 1))
            result += "\n\nРезультаты выполнения задач:" + "".join(f"\n{i}. {answer}" for i, answer in enumerate(answers, 1))
            self.llm_monitoring.update_span(span, metadata={"system_message": self.system_message, "failed_tasks": failures})
            self.llm_monitoring.event(name="final-output", trace_id=trace.id, parent_observation_id=trace.id,
                                      input={"tasks_results": answers}, output={"answer": result})
            self.llm_monitoring.update_trace(trace, output={"answer": result})
            return result
        finally:
            self.llm_monitoring.end_span(span)
