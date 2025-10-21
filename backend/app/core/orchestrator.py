import asyncio
from typing import Dict, Callable, Awaitable
from backend.app.services.report_service import save_report_data

class Orchestrator:
    def __init__(self):
        self.registered_agents: Dict[str, Callable[[str, str], Awaitable[Dict]]] = {}

    def register_agent(self, name: str, agent_func: Callable[[str, str], Awaitable[Dict]]):
        self.registered_agents[name] = agent_func

    async def execute_agents_concurrently(self, report_id: str, token_id: str):
        agent_tasks = []
        agent_names = []

        for name, agent_func in self.registered_agents.items():
            agent_names.append(name)
            agent_tasks.append(self._run_agent_safely(name, agent_func, report_id, token_id))

        results = await asyncio.gather(*agent_tasks, return_exceptions=True)

        aggregated_results = {}
        for i, result in enumerate(results):
            agent_name = agent_names[i]
            if isinstance(result, Exception):
                print(f"Agent '{agent_name}' failed with error: {result}")
                aggregated_results[agent_name] = {"status": "failed", "error": str(result)}
            else:
                aggregated_results[agent_name] = {"status": "completed", "data": result}

        await save_report_data(report_id, {"agent_results": aggregated_results, "status": "completed"})

    async def _run_agent_safely(self, name: str, agent_func: Callable[[str, str], Awaitable[Dict]], report_id: str, token_id: str) -> Dict:
        try:
            return await agent_func(report_id, token_id)
        except Exception as e:
            print(f"Error running agent '{name}': {e}")
            raise  # Re-raise to be caught by asyncio.gather

orchestrator = Orchestrator()
