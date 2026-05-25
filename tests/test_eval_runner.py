from types import SimpleNamespace

from src.evaluation.eval_runner import load_test_cases, run_evaluation


def test_load_test_cases():
    test_cases = load_test_cases()

    assert len(test_cases) >= 8
    assert {"question", "expected_intent", "expected_tools", "required_sections"} <= set(
        test_cases[0]
    )


def test_run_evaluation_limit_one_returns_summary():
    def fake_agent_runner(question):
        return SimpleNamespace(
            intent="churn_analysis",
            selected_tools=["rag_search", "sql_query", "python_analysis"],
            final_report="Evidence / 证据\nKey Findings / 关键发现\nLimitations / 限制说明",
        )

    summary = run_evaluation(limit=1, agent_runner=fake_agent_runner)

    assert summary["total_cases"] == 1
    assert "intent_accuracy" in summary
    assert "avg_tool_selection_score" in summary
    assert "avg_section_completeness_score" in summary
    assert "total_time_seconds" in summary
