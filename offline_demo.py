"""Exercise the real orchestration with explicit deterministic provider test doubles."""
import json
from types import SimpleNamespace
from src.core.agents.summarization import SummarizationAgent, SummarizationDTO

class LocalMonitor:
    def __init__(self): self.closed_spans=0; self.closed_generations=0
    def trace(self, **kwargs): return SimpleNamespace(id="local-trace")
    def span(self, **kwargs): return SimpleNamespace(id="local-span")
    def generation(self, **kwargs): return SimpleNamespace(id="local-generation")
    def update_trace(self, *args, **kwargs): pass
    def update_span(self, *args, **kwargs): pass
    def update_generation(self, *args, **kwargs): pass
    def event(self, *args, **kwargs): pass
    def end_span(self, *args, **kwargs): self.closed_spans+=1
    def end_generation(self, *args, **kwargs): self.closed_generations+=1

class FixtureProvider:
    model_params=None
    system_message="Deterministic offline fixture; no model inference."
    def __init__(self, fail=False): self.fail=fail
    def generate(self,prompt):
        if self.fail: raise TimeoutError("fixture outage")
        return "Demo owner: Anna. Demo deadline: Monday."

def run():
    monitor=LocalMonitor()
    answer=SummarizationAgent(monitor,{"first":FixtureProvider(True),"fallback":FixtureProvider()}).execute(
        SummarizationDTO(user_id="demo-user",text="Anna will send the report on Monday.",tasks=["Identify owner and deadline"]))
    return {"mode":"offline-provider-fixtures","summary":answer,"closed_spans":monitor.closed_spans,
            "closed_generations":monitor.closed_generations,"llm_quality_evaluated":False}

if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2))
