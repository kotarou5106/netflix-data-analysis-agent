from src.nodes.report_writer import write_report
from src.state import AgentState


def test_report_writer_includes_fixed_sections():
    state = AgentState(
        user_query="分析流失率",
        intent="churn_analysis",
        plan=[
            {
                "step_id": "step_1",
                "tool": "rag_search",
                "description": "检索流失分析口径",
                "depends_on": [],
            }
        ],
        selected_tools=["rag_search"],
    )

    report_state = write_report(state)
    report = report_state.draft_report

    assert "# Analysis Report / 分析报告" in report
    assert "## User Question / 用户问题" in report
    assert "## Intent / 意图" in report
    assert "## Analysis Plan / 分析计划" in report
    assert "## Tools Used / 使用工具" in report
    assert "## Evidence / 证据" in report
    assert "## Key Findings / 关键发现" in report
    assert "## Business Suggestions / 业务建议" in report
    assert "## Limitations / 限制说明" in report


def test_report_writer_writes_tool_result_evidence():
    state = AgentState(
        user_query="完播率是什么意思",
        intent="metric_explanation",
        selected_tools=["rag_search"],
        tool_results=[
            {
                "step_id": "step_1",
                "tool": "rag_search",
                "status": "success",
                "result": [
                    {
                        "source": "metric_definitions.md",
                        "content": "Completion Rate / 完播率",
                        "score": 3.0,
                    }
                ],
            }
        ],
    )

    report_state = write_report(state)

    assert "Source: `metric_definitions.md`" in report_state.draft_report
    assert "Completion Rate / 完播率" in report_state.draft_report


def test_report_writer_includes_sql_columns_rows_and_count():
    state = AgentState(
        user_query="分析不同订阅类型的流失率",
        intent="churn_analysis",
        selected_tools=["sql_query"],
        tool_results=[
            {
                "step_id": "step_2",
                "tool": "sql_query",
                "status": "success",
                "result": {
                    "success": True,
                    "columns": ["subscription_type", "user_count", "churn_rate"],
                    "rows": [("Basic", 100, 0.25), ("Premium", 80, 0.10)],
                    "row_count": 2,
                    "error_type": None,
                    "message": "Query executed successfully.",
                    "executed_sql": "SELECT ...",
                },
            }
        ],
    )

    report = write_report(state).draft_report

    assert "Columns: subscription_type, user_count, churn_rate" in report
    assert "Row count: 2" in report
    assert "subscription_type=Basic" in report
    assert "churn_rate=0.2500" in report


def test_report_writer_includes_python_analysis_stats():
    state = AgentState(
        user_query="分析不同订阅类型的流失率",
        intent="churn_analysis",
        selected_tools=["python_analysis"],
        tool_results=[
            {
                "step_id": "step_3",
                "tool": "python_analysis",
                "status": "success",
                "result": {
                    "success": True,
                    "result": [
                        {"group": "Basic", "count": 1, "avg": 0.25, "min": 0.25, "max": 0.25}
                    ],
                    "error_type": None,
                    "message": "Group summary calculated.",
                },
            }
        ],
    )

    report = write_report(state).draft_report

    assert "group=Basic" in report
    assert "count=1" in report
    assert "avg=0.2500" in report


def test_report_writer_does_not_include_typo_suggestn():
    state = AgentState(user_query="分析用户观看行为", intent="general_analysis")

    report = write_report(state).draft_report

    assert "suggestn" not in report
    assert "not as confirmed causal claims" in report
