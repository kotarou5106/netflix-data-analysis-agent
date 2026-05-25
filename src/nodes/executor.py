from typing import Any

from src.nodes.tool_router import SUPPORTED_TOOLS, route_tools
from src.state import AgentState
from src.tools.python_analysis_tool import summarize_by_group
from src.tools.rag_tool import search_knowledge
from src.tools.sql_tool import inspect_schema, run_sql


EXECUTOR_TOOLS = {"rag_search", "sql_query", "python_analysis"}


def execute_plan(state: AgentState) -> AgentState:
    route_tools(state)

    for step in state.plan:
        tool = step.get("tool")
        if tool not in SUPPORTED_TOOLS:
            message = f"Unsupported tool: {tool}"
            state.errors.append(message)
            _append_result(state, step, "error", {"success": False, "message": message})
            continue

        if tool not in state.selected_tools or tool not in EXECUTOR_TOOLS:
            continue

        try:
            if tool == "rag_search":
                result = search_knowledge(state.user_query, top_k=3)
                _append_result(state, step, "success", result)
            elif tool == "sql_query":
                result = _execute_sql_for_intent(state.intent)
                status = "success" if result.get("success") else "error"
                _append_result(state, step, status, result)
                if not result.get("success"):
                    state.errors.append(result.get("message", "SQL query failed."))
            elif tool == "python_analysis":
                result = _execute_python_analysis(state)
                status = "success" if result.get("success") else "error"
                _append_result(state, step, status, result)
                if not result.get("success"):
                    state.errors.append(result.get("message", "Python analysis failed."))
        except Exception as exc:
            message = f"{tool} failed: {exc}"
            state.errors.append(message)
            _append_result(
                state,
                step,
                "error",
                {
                    "success": False,
                    "error_type": type(exc).__name__,
                    "message": message,
                },
            )

    return state


def _execute_python_analysis(state: AgentState) -> dict[str, Any]:
    sql_result = _latest_successful_sql_result(state)
    if not sql_result:
        return {
            "success": False,
            "result": None,
            "error_type": "NO_SQL_RESULT",
            "message": "No successful SQL result is available for python_analysis.",
        }

    rows = _rows_as_dicts(sql_result)
    if not rows:
        return {
            "success": False,
            "result": None,
            "error_type": "EMPTY_ROWS",
            "message": "SQL result has no rows for python_analysis.",
        }

    sample = rows[0]
    if "subscription_type" in sample and "churn_rate" in sample:
        return summarize_by_group(rows, "subscription_type", "churn_rate")

    return {
        "success": False,
        "result": None,
        "error_type": "NO_APPLICABLE_ANALYSIS",
        "message": "SQL result fields are not suitable for the current fixed python_analysis templates.",
    }


def _latest_successful_sql_result(state: AgentState) -> dict[str, Any] | None:
    for item in reversed(state.tool_results):
        if item.get("tool") == "sql_query" and item.get("status") == "success":
            result = item.get("result")
            if isinstance(result, dict) and result.get("success"):
                return result
    return None


def _rows_as_dicts(sql_result: dict[str, Any]) -> list[dict[str, Any]]:
    columns = sql_result.get("columns", [])
    rows = sql_result.get("rows", [])
    return [dict(zip(columns, row)) for row in rows]


def _execute_sql_for_intent(intent: str) -> dict[str, Any]:
    schema = inspect_schema()
    if not schema.get("success"):
        return schema

    fields = _schema_fields(schema)
    sql_error = _validate_sql_fields(intent, fields)
    if sql_error:
        return sql_error

    sql = _sql_template(intent)
    return run_sql(sql)


def _schema_fields(schema: dict[str, Any]) -> set[str]:
    return {row["field_name"] for row in schema.get("rows", []) if "field_name" in row}


def _validate_sql_fields(intent: str, fields: set[str]) -> dict[str, Any] | None:
    required_fields = {
        "churn_analysis": {"subscription_type", "churned"},
        "user_segmentation": {"avg_watch_time_minutes", "churned"},
        "general_analysis": set(),
    }.get(intent, set())

    missing_fields = sorted(required_fields - fields)
    if not missing_fields:
        return None

    return {
        "success": False,
        "columns": [],
        "rows": [],
        "row_count": 0,
        "error_type": "MISSING_FIELDS",
        "message": f"Required fields are missing from schema: {', '.join(missing_fields)}",
        "executed_sql": None,
    }


def _sql_template(intent: str) -> str:
    if intent == "churn_analysis":
        return """
            SELECT
                subscription_type,
                COUNT(*) AS user_count,
                AVG(
                    CASE
                        WHEN lower(CAST(churned AS VARCHAR)) IN ('yes', 'true', '1') THEN 1
                        ELSE 0
                    END
                ) AS churn_rate
            FROM users
            GROUP BY subscription_type
            ORDER BY churn_rate DESC, user_count DESC
        """

    if intent == "user_segmentation":
        return """
            SELECT
                COUNT(*) AS user_count,
                AVG(avg_watch_time_minutes) AS avg_watch_time_minutes,
                AVG(
                    CASE
                        WHEN lower(CAST(churned AS VARCHAR)) IN ('yes', 'true', '1') THEN 1
                        ELSE 0
                    END
                ) AS avg_churn_flag
            FROM users
        """

    return "SELECT * FROM users LIMIT 10"


def _append_result(
    state: AgentState,
    step: dict[str, Any],
    status: str,
    result: Any,
) -> None:
    state.tool_results.append(
        {
            "step_id": step.get("step_id"),
            "tool": step.get("tool"),
            "status": status,
            "result": result,
        }
    )
