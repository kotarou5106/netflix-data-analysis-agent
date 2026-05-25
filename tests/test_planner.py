from src.nodes.planner import plan_task


def test_churn_query_gets_churn_analysis_intent():
    state = plan_task("分析不同订阅类型的流失率")

    assert state.intent == "churn_analysis"
    assert _tools(state.plan) == [
        "rag_search",
        "sql_query",
        "python_analysis",
        "report_writer",
        "verifier",
    ]


def test_metric_query_gets_metric_explanation_intent():
    state = plan_task("完播率是什么意思")

    assert state.intent == "metric_explanation"
    assert _tools(state.plan) == ["rag_search", "report_writer"]


def test_segmentation_query_gets_user_segmentation_intent():
    state = plan_task("把用户分层")

    assert state.intent == "user_segmentation"
    assert _tools(state.plan) == [
        "rag_search",
        "sql_query",
        "python_analysis",
        "report_writer",
        "verifier",
    ]


def test_general_query_gets_general_analysis_intent():
    state = plan_task("分析用户观看行为")

    assert state.intent == "general_analysis"
    assert _tools(state.plan) == ["rag_search", "sql_query", "report_writer"]


def test_each_plan_step_has_required_fields():
    state = plan_task("分析不同订阅类型的流失率")

    for step in state.plan:
        assert "step_id" in step
        assert "tool" in step
        assert "description" in step
        assert "depends_on" in step


def _tools(plan):
    return [step["tool"] for step in plan]
