from src.nodes.executor import execute_plan
from src.nodes.planner import plan_task
from src.state import AgentState


def test_executor_can_execute_rag_search():
    state = execute_plan(plan_task("完播率是什么意思"))

    rag_results = [result for result in state.tool_results if result["tool"] == "rag_search"]
    assert rag_results
    assert rag_results[0]["status"] == "success"
    assert isinstance(rag_results[0]["result"], list)


def test_executor_can_execute_sql_query_or_structured_error():
    state = execute_plan(plan_task("分析不同订阅类型的流失率"))

    sql_results = [result for result in state.tool_results if result["tool"] == "sql_query"]
    assert sql_results

    sql_result = sql_results[0]["result"]
    assert "success" in sql_result
    assert "columns" in sql_result
    assert "rows" in sql_result
    assert "row_count" in sql_result
    assert "error_type" in sql_result
    assert "message" in sql_result
    assert "executed_sql" in sql_result


def test_executor_does_not_crash_when_a_step_fails():
    state = AgentState(
        user_query="测试失败步骤",
        intent="general_analysis",
        plan=[
            {
                "step_id": "step_1",
                "tool": "unknown_tool",
                "description": "未知工具",
                "depends_on": [],
            },
            {
                "step_id": "step_2",
                "tool": "report_writer",
                "description": "后续阶段生成报告",
                "depends_on": ["step_1"],
            },
        ],
    )

    executed_state = execute_plan(state)

    assert executed_state.tool_results
    assert any(result["status"] == "error" for result in executed_state.tool_results)


def test_executor_churn_analysis_does_not_write_report_or_verifier_skips():
    state = execute_plan(plan_task("分析不同订阅类型的流失率"))

    tools = [result["tool"] for result in state.tool_results]
    assert "report_writer" not in tools
    assert "verifier" not in tools
    assert not any(result["status"] == "skipped" for result in state.tool_results)


def test_executor_churn_analysis_produces_rag_and_sql_results():
    state = execute_plan(plan_task("分析不同订阅类型的流失率"))

    tools = [result["tool"] for result in state.tool_results]
    assert "rag_search" in tools
    assert "sql_query" in tools
