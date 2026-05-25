from src.graph import run_agent


def test_run_agent_returns_state_with_final_report():
    state = run_agent("分析用户观看行为")

    assert state.final_report


def test_churn_query_sets_churn_analysis_intent():
    state = run_agent("分析不同订阅类型的流失率")

    assert state.intent == "churn_analysis"


def test_final_report_contains_analysis_report_title():
    state = run_agent("分析用户观看行为")

    assert "Analysis Report / 分析报告" in state.final_report
