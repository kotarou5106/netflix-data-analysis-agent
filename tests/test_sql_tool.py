from src.tools.sql_tool import inspect_schema, run_sql


def test_select_can_execute():
    result = run_sql("SELECT * FROM users LIMIT 5")

    assert result["success"] is True
    assert "user_id" in result["columns"]
    assert result["row_count"] <= 5
    assert result["rows"]
    assert "LIMIT 100" in result["executed_sql"]


def test_drop_is_rejected():
    result = run_sql("DROP TABLE users")

    assert result["success"] is False
    assert result["error_type"] == "NON_SELECT_REJECTED"
    assert result["rows"] == []


def test_inspect_schema_returns_field_information():
    result = inspect_schema()

    assert result["success"] is True
    assert result["columns"] == ["field_name", "field_type"]
    assert result["row_count"] > 0
    fields = [row["field_name"] for row in result["rows"]]
    assert "user_id" in fields


def test_missing_field_returns_structured_error():
    result = run_sql("SELECT nonexistent_column FROM users LIMIT 1")

    assert result["success"] is False
    assert result["columns"] == []
    assert result["rows"] == []
    assert result["row_count"] == 0
    assert result["error_type"]
    assert result["message"]
    assert "nonexistent_column" in result["executed_sql"]
