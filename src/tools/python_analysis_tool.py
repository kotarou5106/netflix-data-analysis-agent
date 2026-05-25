import math
from collections import defaultdict
from typing import Any


def summarize_by_group(rows: list[dict[str, Any]], group_key: str, metric_key: str) -> dict[str, Any]:
    validation_error = _validate_keys(rows, [group_key, metric_key])
    if validation_error:
        return validation_error

    grouped_values: dict[Any, list[float]] = defaultdict(list)
    for row in rows:
        value = _to_number(row.get(metric_key))
        if value is None:
            return _error("NON_NUMERIC_FIELD", f"Field is not numeric: {metric_key}")
        grouped_values[row.get(group_key)].append(value)

    result = []
    for group, values in grouped_values.items():
        result.append(
            {
                "group": group,
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
        )

    return _success(result, "Group summary calculated.")


def calculate_churn_rate(rows: list[dict[str, Any]], group_key: str, churn_key: str) -> dict[str, Any]:
    validation_error = _validate_keys(rows, [group_key, churn_key])
    if validation_error:
        return validation_error

    grouped_values: dict[Any, list[int]] = defaultdict(list)
    for row in rows:
        churn_value = _to_churn_flag(row.get(churn_key))
        if churn_value is None:
            return _error("INVALID_CHURN_VALUE", f"Field cannot be converted to churn flag: {churn_key}")
        grouped_values[row.get(group_key)].append(churn_value)

    result = []
    for group, values in grouped_values.items():
        user_count = len(values)
        result.append(
            {
                "group": group,
                "user_count": user_count,
                "churn_rate": sum(values) / user_count if user_count else 0,
            }
        )

    return _success(result, "Churn rate calculated.")


def basic_correlation(rows: list[dict[str, Any]], x_key: str, y_key: str) -> dict[str, Any]:
    validation_error = _validate_keys(rows, [x_key, y_key])
    if validation_error:
        return validation_error

    x_values = []
    y_values = []
    for row in rows:
        x_value = _to_number(row.get(x_key))
        y_value = _to_number(row.get(y_key))
        if x_value is None or y_value is None:
            return _error("NON_NUMERIC_FIELD", f"Fields must be numeric: {x_key}, {y_key}")
        x_values.append(x_value)
        y_values.append(y_value)

    if len(x_values) < 2:
        return _error("INSUFFICIENT_DATA", "At least two rows are required to calculate correlation.")

    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    x_variance = sum((x - x_mean) ** 2 for x in x_values)
    y_variance = sum((y - y_mean) ** 2 for y in y_values)

    denominator = math.sqrt(x_variance * y_variance)
    if denominator == 0:
        return _error("ZERO_VARIANCE", "Correlation cannot be calculated when a field has zero variance.")

    return _success({"correlation": numerator / denominator}, "Correlation calculated.")


def _validate_keys(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, Any] | None:
    if not rows:
        return _error("EMPTY_ROWS", "Rows cannot be empty.")

    for row in rows:
        for key in keys:
            if key not in row:
                return _error("MISSING_FIELD", f"Missing field: {key}")

    return None


def _to_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _to_churn_flag(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in {0, 1}:
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return 1
        if normalized in {"0", "false", "no", "n"}:
            return 0
    return None


def _success(result: Any, message: str) -> dict[str, Any]:
    return {
        "success": True,
        "result": result,
        "error_type": None,
        "message": message,
    }


def _error(error_type: str, message: str) -> dict[str, Any]:
    return {
        "success": False,
        "result": None,
        "error_type": error_type,
        "message": message,
    }
