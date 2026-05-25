from collections.abc import Callable

from src.nodes.executor import execute_plan
from src.nodes.planner import plan_task
from src.nodes.report_writer import write_report
from src.nodes.tool_router import route_tools
from src.nodes.verifier import verify_report
from src.state import AgentState


def run_agent(user_query: str) -> AgentState:
    state = AgentState(user_query=user_query)

    for step in (
        lambda current_state: plan_task(current_state.user_query),
        route_tools,
        execute_plan,
        write_report,
        verify_report,
    ):
        state = _run_step_safely(step, state)

    return state


def _run_step_safely(step: Callable[[AgentState], AgentState], state: AgentState) -> AgentState:
    try:
        return step(state)
    except Exception as exc:
        state.errors.append(f"{step.__name__} failed: {exc}")
        return state
