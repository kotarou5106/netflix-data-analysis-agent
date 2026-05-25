import json

from src.nodes import planner
from src.nodes.planner import plan_task


class FakeLLMClient:
    def __init__(self, output):
        self.output = output

    def generate_plan(self, prompt):
        return self.output


def test_plan_task_falls_back_without_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(planner, "get_llm_client", lambda: None)

    state = plan_task("分析不同订阅类型的流失率")

    assert state.intent == "churn_analysis"
    assert [step["tool"] for step in state.plan] == [
        "rag_search",
        "sql_query",
        "python_analysis",
        "report_writer",
        "verifier",
    ]


def test_invalid_json_falls_back_to_rule_based_planner(monkeypatch):
    monkeypatch.setattr(planner, "get_llm_client", lambda: FakeLLMClient("not json"))

    state = plan_task("完播率是什么意思")

    assert state.intent == "metric_explanation"
    assert [step["tool"] for step in state.plan] == ["rag_search", "report_writer"]


def test_invalid_tool_falls_back_to_rule_based_planner(monkeypatch):
    output = {
        "intent": "metric_explanation",
        "plan": [
            {
                "step_id": "step_1",
                "tool": "unsafe_tool",
                "description": "bad tool",
                "depends_on": [],
            }
        ],
    }
    monkeypatch.setattr(planner, "get_llm_client", lambda: FakeLLMClient(json.dumps(output)))

    state = plan_task("完播率是什么意思")

    assert state.intent == "metric_explanation"
    assert [step["tool"] for step in state.plan] == ["rag_search", "report_writer"]


def test_valid_mock_llm_output_generates_plan(monkeypatch):
    output = {
        "intent": "general_analysis",
        "plan": [
            {
                "step_id": "step_1",
                "tool": "rag_search",
                "description": "检索相关业务知识",
                "depends_on": [],
            },
            {
                "step_id": "step_2",
                "tool": "report_writer",
                "description": "生成回答",
                "depends_on": ["step_1"],
            },
        ],
    }
    monkeypatch.setattr(planner, "get_llm_client", lambda: FakeLLMClient(json.dumps(output)))

    state = plan_task("请总结这个数据集")

    assert state.intent == "general_analysis"
    assert [step["tool"] for step in state.plan] == ["rag_search", "report_writer"]
