import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from src.llm import get_llm_client
from src.state import AgentState


VALID_INTENTS = {
    "churn_analysis",
    "metric_explanation",
    "user_segmentation",
    "general_analysis",
}

VALID_TOOLS = {
    "rag_search",
    "sql_query",
    "python_analysis",
    "report_writer",
    "verifier",
}


class PlanStep(BaseModel):
    step_id: str
    tool: str
    description: str
    depends_on: list[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    intent: str
    plan: list[PlanStep]


def plan_task(user_query: str) -> AgentState:
    llm_state = llm_plan_task(user_query)
    if llm_state is not None:
        return llm_state

    return rule_based_plan_task(user_query)


def rule_based_plan_task(user_query: str) -> AgentState:
    intent = _identify_intent(user_query)
    plan = _build_plan(intent)

    return AgentState(
        user_query=user_query,
        intent=intent,
        plan=plan,
        selected_tools=[step["tool"] for step in plan],
    )


def llm_plan_task(user_query: str) -> AgentState | None:
    client = get_llm_client()
    if client is None:
        return None

    try:
        raw_output = client.generate_plan(_build_llm_prompt(user_query))
    except Exception:
        return None

    parsed_output = _parse_llm_output(raw_output)
    if parsed_output is None or not _is_valid_planner_output(parsed_output):
        return None

    plan = [step.model_dump() if hasattr(step, "model_dump") else step.dict() for step in parsed_output.plan]
    return AgentState(
        user_query=user_query,
        intent=parsed_output.intent,
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


def _build_llm_prompt(user_query: str) -> str:
    return f"""
You are the planner for a Netflix user behavior analysis agent.
Return only JSON with this schema:
{{
  "intent": "churn_analysis | metric_explanation | user_segmentation | general_analysis",
  "plan": [
    {{
      "step_id": "step_1",
      "tool": "rag_search | sql_query | python_analysis | report_writer | verifier",
      "description": "short description",
      "depends_on": []
    }}
  ]
}}

Allowed intents: {sorted(VALID_INTENTS)}
Allowed tools: {sorted(VALID_TOOLS)}

Do not write SQL. Do not execute tools. Only create a structured plan.

User question: {user_query}
""".strip()


def _parse_llm_output(raw_output: Any) -> PlannerOutput | None:
    if raw_output is None:
        return None

    try:
        payload = raw_output if isinstance(raw_output, dict) else json.loads(raw_output)
        if hasattr(PlannerOutput, "model_validate"):
            return PlannerOutput.model_validate(payload)
        return PlannerOutput.parse_obj(payload)
    except (TypeError, json.JSONDecodeError, ValidationError):
        return None


def _is_valid_planner_output(output: PlannerOutput) -> bool:
    if output.intent not in VALID_INTENTS:
        return False
    if not output.plan:
        return False
    return all(step.tool in VALID_TOOLS for step in output.plan)
