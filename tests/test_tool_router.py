from src.nodes.planner import plan_task
from src.nodes.tool_router import route_tools


def test_churn_analysis_selects_rag_and_sql():
    state = route_tools(plan_task("分析不同订阅类型的流失率"))

    assert "rag_search" in state.selected_tools
    assert "sql_query" in state.selected_tools


def test_metric_explanation_does_not_select_sql():
    state = route_tools(plan_task("完播率是什么意思"))

    assert state.selected_tools == ["rag_search", "report_writer"]
    assert "sql_query" not in state.selected_tools
