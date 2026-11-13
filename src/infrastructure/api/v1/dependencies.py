from functools import lru_cache

@lru_cache
def get_summarizer_agents():
    # Defer SDK loading and client construction until an actual live request.
    from src.infrastructure.providers import OpenAIProvider, YandexProvider, DeepSeekProvider
    from src.core.prompts import SUMMARIZATION_PROMPT
    return {"openai": OpenAIProvider(SUMMARIZATION_PROMPT), "yandex": YandexProvider(SUMMARIZATION_PROMPT),
            "deepseek": DeepSeekProvider(SUMMARIZATION_PROMPT)}

@lru_cache
def get_llm_monitoring():
    from src.infrastructure.llm_monitoring import LangfuseProvider
    return LangfuseProvider()
