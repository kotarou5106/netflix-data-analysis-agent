from typing import Any

from src.state import AgentState


def write_report(state: AgentState) -> AgentState:
    report = "\n\n".join(
        [
            "# Analysis Report / 分析报告",
            "## User Question / 用户问题\n\n" + _text_or_placeholder(state.user_query),
            "## Intent / 意图\n\n" + _text_or_placeholder(state.intent),
            "## Analysis Plan / 分析计划\n\n" + _format_plan(state.plan),
            "## Tools Used / 使用工具\n\n" + _format_tools(state.selected_tools),
            "## Evidence / 证据\n\n" + _format_evidence(state.tool_results),
            "## Key Findings / 关键发现\n\n" + _format_findings(state.tool_results),
            "## Business Suggestions / 业务建议\n\n" + _format_suggestions(state.intent),
            "## Limitations / 限制说明\n\n" + _format_limitations(state),
        ]
    )

    state.draft_report = report
    return state


def _format_plan(plan: list[dict[str, Any]]) -> str:
    if not plan:
        return "- No plan was provided."

    lines = []
    for step in plan:
        lines.append(
            f"- {step.get('step_id', 'unknown')}: {step.get('tool', 'unknown')} - "
            f"{step.get('description', '')}"
        )
    return "\n".join(lines)


def _format_tools(selected_tools: list[str]) -> str:
    if not selected_tools:
        return "- No tools were selected."
    return "\n".join(f"- {tool}" for tool in selected_tools)


def _format_evidence(tool_results: list[dict[str, Any]]) -> str:
    if not tool_results:
        return "- No tool evidence is available yet."

    evidence = []
    for item in tool_results:
        tool = item.get("tool", "unknown")
        status = item.get("status", "unknown")
        result = item.get("result")
        evidence.append(f"### {tool} ({status})")
        evidence.append(_format_tool_evidence(tool, result))
    return "\n".join(evidence)


def _format_findings(tool_results: list[dict[str, Any]]) -> str:
    findings = []

    for item in tool_results:
        if item.get("status") != "success":
            continue
        result = item.get("result")
        if item.get("tool") == "sql_query":
            findings.extend(_sql_findings(result))
        elif item.get("tool") == "python_analysis":
            findings.extend(_analysis_findings(result))

    if not findings:
        return "- 当前结果需要进一步人工解读，暂不能形成明确业务结论。"

    return "\n".join(findings)


def _format_suggestions(intent: str) -> str:
    if intent == "metric_explanation":
        return "- Use the project metric definitions when explaining results."
    if intent == "churn_analysis":
        return "- Treat high-risk groups as potentially associated with higher churn risk and validate actions with follow-up analysis."
    if intent == "user_segmentation":
        return "- Treat segmentation rules as project assumptions and review thresholds with business context."
    return "- Base business suggestions on observed data evidence and project knowledge definitions."


def _format_limitations(state: AgentState) -> str:
    limitations = [
        "- This report is based on observational analysis and must not describe correlation as causation.",
        "- Business suggestions should be treated as hypotheses supported by available evidence, not as confirmed causal claims.",
    ]

    errors = list(state.errors)
    for item in state.tool_results:
        result = item.get("result")
        if item.get("status") == "error":
            errors.append(_extract_message(result))

    if errors:
        limitations.append("- Tool errors or incomplete results: " + "; ".join(error for error in errors if error))

    return "\n".join(limitations)


def _format_tool_evidence(tool: str, result: Any) -> str:
    if tool == "rag_search":
        return _format_rag_evidence(result)
    if tool == "sql_query":
        return _format_sql_evidence(result)
    if tool == "python_analysis":
        return _format_python_analysis_evidence(result)
    return f"- {_summarize_result(result)}"


def _format_rag_evidence(result: Any) -> str:
    if not isinstance(result, list) or not result:
        return "- No knowledge base snippets were returned."

    lines = []
    for item in result:
        source = item.get("source", "unknown")
        content = _shorten(str(item.get("content", "")), 180)
        lines.append(f"- Source: `{source}` - {content}")
    return "\n".join(lines)


def _format_sql_evidence(result: Any) -> str:
    if not isinstance(result, dict):
        return "- SQL result was not structured."
    if not result.get("success"):
        return f"- SQL error: {result.get('message', 'Unknown error.')}"

    columns = result.get("columns", [])
    rows = result.get("rows", [])
    row_count = result.get("row_count", 0)
    lines = [
        f"- Columns: {', '.join(str(column) for column in columns)}",
        f"- Row count: {row_count}",
        "- Preview rows:",
    ]
    for row in rows[:5]:
        lines.append(f"  - {_format_row(columns, row)}")
    return "\n".join(lines)


def _format_python_analysis_evidence(result: Any) -> str:
    if not isinstance(result, dict):
        return "- Python analysis result was not structured."
    if not result.get("success"):
        return f"- Python analysis error: {result.get('message', 'Unknown error.')}"

    analysis_result = result.get("result")
    if isinstance(analysis_result, list):
        lines = []
        for item in analysis_result[:5]:
            lines.append("- " + _format_analysis_item(item))
        return "\n".join(lines)
    if isinstance(analysis_result, dict):
        return "- " + _format_analysis_item(analysis_result)
    return f"- {analysis_result}"


def _sql_findings(result: Any) -> list[str]:
    if not isinstance(result, dict) or not result.get("success"):
        return []

    columns = result.get("columns", [])
    rows = result.get("rows", [])
    if "subscription_type" not in columns or "churn_rate" not in columns or not rows:
        return []

    subscription_index = columns.index("subscription_type")
    churn_index = columns.index("churn_rate")
    sorted_rows = sorted(rows, key=lambda row: row[churn_index], reverse=True)
    top_row = sorted_rows[0]
    low_row = sorted_rows[-1]
    return [
        "- Observed churn rates differ by subscription type; "
        f"`{top_row[subscription_index]}` is highest in the current result at {_format_number(top_row[churn_index])}, "
        f"while `{low_row[subscription_index]}` is lowest at {_format_number(low_row[churn_index])}. "
        "This indicates a high-risk group, not a confirmed causal relationship."
    ]


def _analysis_findings(result: Any) -> list[str]:
    if not isinstance(result, dict) or not result.get("success"):
        return []

    analysis_result = result.get("result")
    if not isinstance(analysis_result, list) or not analysis_result:
        return []

    first_item = analysis_result[0]
    if "group" in first_item and "avg" in first_item:
        sorted_items = sorted(analysis_result, key=lambda item: item.get("avg", 0), reverse=True)
        top_item = sorted_items[0]
        return [
            "- Python analysis shows grouped statistical differences; "
            f"`{top_item.get('group')}` has the highest observed average at {_format_number(top_item.get('avg'))}."
        ]
    if "group" in first_item and "churn_rate" in first_item:
        sorted_items = sorted(analysis_result, key=lambda item: item.get("churn_rate", 0), reverse=True)
        top_item = sorted_items[0]
        return [
            "- Python analysis shows grouped churn-rate differences; "
            f"`{top_item.get('group')}` has the highest observed churn rate at {_format_number(top_item.get('churn_rate'))}."
        ]
    return []


def _format_row(columns: list[Any], row: Any) -> str:
    if isinstance(row, dict):
        return ", ".join(f"{key}={_format_number(value)}" for key, value in row.items())
    return ", ".join(
        f"{column}={_format_number(value)}"
        for column, value in zip(columns, row)
    )


def _format_analysis_item(item: Any) -> str:
    if not isinstance(item, dict):
        return str(item)
    preferred_keys = ["group", "count", "user_count", "avg", "churn_rate", "min", "max"]
    parts = []
    for key in preferred_keys:
        if key in item:
            parts.append(f"{key}={_format_number(item[key])}")
    if parts:
        return ", ".join(parts)
    return ", ".join(f"{key}={_format_number(value)}" for key, value in item.items())


def _format_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _shorten(text: str, max_length: int) -> str:
    compact_text = " ".join(text.split())
    if len(compact_text) <= max_length:
        return compact_text
    return compact_text[: max_length - 3] + "..."


def _summarize_result(result: Any) -> str:
    if isinstance(result, list):
        return f"{len(result)} item(s) returned."
    if isinstance(result, dict):
        if "message" in result:
            return str(result["message"])
        if "row_count" in result:
            return f"{result['row_count']} row(s) returned."
        if "result" in result:
            return str(result["result"])
    return _text_or_placeholder(str(result))


def _extract_message(result: Any) -> str:
    if isinstance(result, dict):
        return str(result.get("message", "Unknown tool error."))
    return "Unknown tool error."


def _text_or_placeholder(value: str) -> str:
    return value if value else "N/A"
