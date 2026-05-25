from src.state import AgentState


def plan_task(user_query: str) -> AgentState:
    intent = _identify_intent(user_query)
    plan = _build_plan(intent)

    return AgentState(
        user_query=user_query,
        intent=intent,
        plan=plan,
        selected_tools=[step["tool"] for step in plan],
    )


def _identify_intent(user_query: str) -> str:
    normalized_query = user_query.lower()

    if "流失" in user_query or "churn" in normalized_query:
        return "churn_analysis"
    if (
        "指标" in user_query
        or "定义" in user_query
        or "是什么意思" in user_query
        or "rate" in normalized_query
    ):
        return "metric_explanation"
    if "分层" in user_query or "用户群体" in user_query or "segmentation" in normalized_query:
        return "user_segmentation"
    return "general_analysis"


def _build_plan(intent: str) -> list[dict[str, object]]:
    if intent == "churn_analysis":
        return [
            _step("step_1", "rag_search", "检索流失分析口径和限制说明。", []),
            _step("step_2", "sql_query", "查询流失相关数据和维度统计。", ["step_1"]),
            _step("step_3", "python_analysis", "对流失数据进行统计分析。", ["step_2"]),
            _step("step_4", "report_writer", "基于证据生成流失分析报告。", ["step_1", "step_3"]),
            _step("step_5", "verifier", "校验报告结论是否符合数据证据和知识库口径。", ["step_4"]),
        ]

    if intent == "metric_explanation":
        return [
            _step("step_1", "rag_search", "检索指标定义和项目分析口径。", []),
            _step("step_2", "report_writer", "生成指标解释说明。", ["step_1"]),
        ]

    if intent == "user_segmentation":
        return [
            _step("step_1", "rag_search", "检索用户分层规则和项目假设。", []),
            _step("step_2", "sql_query", "查询用户分层相关数据字段。", ["step_1"]),
            _step("step_3", "python_analysis", "根据项目假设进行用户分层统计。", ["step_2"]),
            _step("step_4", "report_writer", "生成用户分层分析报告。", ["step_1", "step_3"]),
            _step("step_5", "verifier", "校验分层结论是否符合数据证据和知识库口径。", ["step_4"]),
        ]

    return [
        _step("step_1", "rag_search", "检索与问题相关的业务知识。", []),
        _step("step_2", "sql_query", "查询回答问题所需的数据。", ["step_1"]),
        _step("step_3", "report_writer", "基于知识库和数据结果生成分析回答。", ["step_1", "step_2"]),
    ]


def _step(step_id: str, tool: str, description: str, depends_on: list[str]) -> dict[str, object]:
    return {
        "step_id": step_id,
        "tool": tool,
        "description": description,
        "depends_on": depends_on,
    }
