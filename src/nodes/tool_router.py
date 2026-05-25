from src.state import AgentState


SUPPORTED_TOOLS = {
    "rag_search",
    "sql_query",
    "python_analysis",
    "report_writer",
    "verifier",
}

TOOLS_BY_INTENT = {
    "churn_analysis": [
        "rag_search",
        "sql_query",
        "python_analysis",
        "report_writer",
        "verifier",
    ],
    "metric_explanation": ["rag_search", "report_writer"],
    "user_segmentation": [
        "rag_search",
        "sql_query",
        "python_analysis",
        "report_writer",
        "verifier",
    ],
    "general_analysis": ["rag_search", "sql_query", "report_writer"],
}


def route_tools(state: AgentState) -> AgentState:
    allowed_tools = TOOLS_BY_INTENT.get(state.intent, TOOLS_BY_INTENT["general_analysis"])
    plan_tools = [step.get("tool") for step in state.plan if step.get("tool") in SUPPORTED_TOOLS]

    selected_tools = []
    for tool in plan_tools:
        if tool in allowed_tools and tool not in selected_tools:
            selected_tools.append(tool)

    if not selected_tools:
        selected_tools = allowed_tools.copy()

    state.selected_tools = selected_tools
    return state
