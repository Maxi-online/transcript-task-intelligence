import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from offline_demo import LocalMonitor, FixtureProvider, run
from src.core.agents.summarization import SummarizationAgent, SummarizationDTO, ProvidersUnavailableError
from src.infrastructure.api.v1.routers.agents import router
from src.infrastructure.api.v1.dependencies import get_summarizer_agents, get_llm_monitoring

class OrchestrationTests(unittest.TestCase):
    def test_fallback_closes_both_generations(self):
        result=run();self.assertEqual(result["closed_generations"],2);self.assertEqual(result["closed_spans"],1)
    def test_complete_failure_still_closes_span(self):
        monitor=LocalMonitor()
        with self.assertRaises(ProvidersUnavailableError):
            SummarizationAgent(monitor,{"failed":FixtureProvider(True)}).execute(SummarizationDTO(user_id="demo",text="demo",tasks=["task"]))
        self.assertEqual(monitor.closed_spans,1);self.assertEqual(monitor.closed_generations,1)
    def test_empty_task_list_is_rejected(self):
        with self.assertRaises(ValueError):
            SummarizationAgent(LocalMonitor(),{"fixture":FixtureProvider()}).execute(SummarizationDTO(user_id="demo",text="demo",tasks=[]))
    def test_api_preserves_provider_unavailable_status(self):
        app=FastAPI();app.include_router(router)
        app.dependency_overrides[get_llm_monitoring]=LocalMonitor
        app.dependency_overrides[get_summarizer_agents]=lambda:{"failed":FixtureProvider(True)}
        response=TestClient(app).post("/agents/summarize",json={"user_id":"demo","text":"demo","tasks":["task"]})
        self.assertEqual(response.status_code,503)
    def test_api_returns_actual_summary_schema(self):
        app=FastAPI();app.include_router(router)
        app.dependency_overrides[get_llm_monitoring]=LocalMonitor
        app.dependency_overrides[get_summarizer_agents]=lambda:{"fixture":FixtureProvider()}
        response=TestClient(app).post("/agents/summarize",json={"user_id":"demo","text":"demo","tasks":["task"]})
        self.assertEqual(response.status_code,200);self.assertIn("summary",response.json()["data"])

    def test_actual_app_lifespan_without_provider_credentials(self):
        from main import app
        app.dependency_overrides[get_llm_monitoring]=LocalMonitor
        app.dependency_overrides[get_summarizer_agents]=lambda:{"fixture":FixtureProvider()}
        path=next(r.path for r in app.routes if r.path.endswith("/agents/summarize"))
        try:
            with TestClient(app) as client:
                response=client.post(path,json={"user_id":"demo","text":"demo","tasks":["task"]})
                self.assertEqual(response.status_code,200)
        finally:
            app.dependency_overrides.clear()
