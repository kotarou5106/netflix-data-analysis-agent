from collections.abc import Callable

from src.nodes.executor import execute_plan
from src.nodes.planner import plan_task
from src.nodes.report_writer import write_report
from src.nodes.tool_router import route_tools
from src.nodes.verifier import verify_report
from src.state import AgentState

try:
    from langgraph.graph import END, START, StateGraph
except Exception:
    END = None
    START = None
    StateGraph = None


def run_agent(user_query: str) -> AgentState:
    if StateGraph is not None:
        try:
            return _run_langgraph_pipeline(user_query)
        except Exception:
            pass

    return _run_fallback_pipeline(user_query)


def _run_langgraph_pipeline(user_query: str) -> AgentState:
    workflow = StateGraph(dict)
    workflow.add_node("planner", _planner_node)
    workflow.add_node("tool_router", _tool_router_node)
    workflow.add_node("executor", _executor_node)
    workflow.add_node("report_writer", _report_writer_node)
    workflow.add_node("verifier", _verifier_node)

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "tool_router")
    workflow.add_edge("tool_router", "executor")
    workflow.add_edge("executor", "report_writer")
    workflow.add_edge("report_writer", "verifier")
    workflow.add_edge("verifier", END)

    graph = workflow.compile()
    result = graph.invoke(_state_to_dict(AgentState(user_query=user_query)))
    return _dict_to_state(result)


def _run_fallback_pipeline(user_query: str) -> AgentState:
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


def _planner_node(state_data: dict) -> dict:
    state = _dict_to_state(state_data)
    return _state_to_dict(plan_task(state.user_query))


def _tool_router_node(state_data: dict) -> dict:
    return _state_to_dict(route_tools(_dict_to_state(state_data)))


def _executor_node(state_data: dict) -> dict:
    return _state_to_dict(execute_plan(_dict_to_state(state_data)))


def _report_writer_node(state_data: dict) -> dict:
    return _state_to_dict(write_report(_dict_to_state(state_data)))


def _verifier_node(state_data: dict) -> dict:
    return _state_to_dict(verify_report(_dict_to_state(state_data)))


def _run_step_safely(step: Callable[[AgentState], AgentState], state: AgentState) -> AgentState:
    try:
        return step(state)
    except Exception as exc:
        state.errors.append(f"{step.__name__} failed: {exc}")
        return state


def _state_to_dict(state: AgentState) -> dict:
    if hasattr(state, "model_dump"):
        return state.model_dump()
    return state.dict()


def _dict_to_state(state_data: dict | AgentState) -> AgentState:
    if isinstance(state_data, AgentState):
        return state_data
    return AgentState(**state_data)
