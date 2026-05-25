from src.tools.python_analysis_tool import (
    basic_correlation,
    calculate_churn_rate,
    summarize_by_group,
)


def test_calculate_churn_rate_by_group():
    rows = [
        {"plan": "Basic", "churned": 1},
        {"plan": "Basic", "churned": 0},
        {"plan": "Premium", "churned": True},
    ]

    result = calculate_churn_rate(rows, "plan", "churned")

    assert result["success"] is True
    by_group = {item["group"]: item for item in result["result"]}
    assert by_group["Basic"]["user_count"] == 2
    assert by_group["Basic"]["churn_rate"] == 0.5
    assert by_group["Premium"]["churn_rate"] == 1


def test_summarize_by_group_count_and_avg():
    rows = [
        {"plan": "Basic", "watch_time": 10},
        {"plan": "Basic", "watch_time": 30},
        {"plan": "Premium", "watch_time": 50},
    ]

    result = summarize_by_group(rows, "plan", "watch_time")

    assert result["success"] is True
    by_group = {item["group"]: item for item in result["result"]}
    assert by_group["Basic"]["count"] == 2
    assert by_group["Basic"]["avg"] == 20


def test_basic_correlation_non_numeric_field_returns_structured_error():
    rows = [
        {"watch_time": 10, "segment": "heavy"},
        {"watch_time": 20, "segment": "light"},
    ]

    result = basic_correlation(rows, "watch_time", "segment")

    assert result["success"] is False
    assert result["result"] is None
    assert result["error_type"] == "NON_NUMERIC_FIELD"
    assert result["message"]
