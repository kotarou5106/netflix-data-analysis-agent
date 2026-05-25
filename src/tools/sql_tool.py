import re
from pathlib import Path
from typing import Any

import duckdb

from src.config import NETFLIX_CSV_PATH


DEFAULT_MAX_ROWS = 100
TABLE_NAME = "users"
FORBIDDEN_KEYWORDS = {
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "CREATE",
    "TRUNCATE",
}


def inspect_schema() -> dict[str, Any]:
    query = f"DESCRIBE SELECT * FROM read_csv_auto('{_sql_path(NETFLIX_CSV_PATH)}')"

    try:
        with duckdb.connect(database=":memory:") as connection:
            schema_rows = connection.execute(query).fetchall()

        return {
            "success": True,
            "columns": ["field_name", "field_type"],
            "rows": [
                {"field_name": row[0], "field_type": row[1]}
                for row in schema_rows
            ],
            "row_count": len(schema_rows),
            "error_type": None,
            "message": "Schema inspection succeeded.",
            "executed_sql": query,
        }
    except Exception as exc:
        return _error_result("SCHEMA_ERROR", str(exc), query)


def run_sql(query: str) -> dict[str, Any]:
    validation_error = _validate_query(query)
    if validation_error:
        return _error_result(validation_error, "Only single SELECT or WITH queries are allowed.", query)

    normalized_query = _strip_trailing_semicolon(query.strip())
    executed_sql = f"SELECT * FROM ({normalized_query}) AS result LIMIT {DEFAULT_MAX_ROWS}"

    try:
        with duckdb.connect(database=":memory:") as connection:
            _register_csv_view(connection)
            result = connection.execute(executed_sql)
            columns = [column[0] for column in result.description]
            rows = result.fetchall()

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "error_type": None,
            "message": "Query executed successfully.",
            "executed_sql": executed_sql,
        }
    except Exception as exc:
        return _error_result(type(exc).__name__, str(exc), executed_sql)


def _register_csv_view(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        f"""
        CREATE VIEW {TABLE_NAME} AS
        SELECT * FROM read_csv_auto('{_sql_path(NETFLIX_CSV_PATH)}')
        """
    )


def _validate_query(query: str) -> str | None:
    if not isinstance(query, str) or not query.strip():
        return "EMPTY_QUERY"

    normalized = query.strip()
    statement = _strip_trailing_semicolon(normalized)

    if ";" in statement:
        return "MULTI_STATEMENT_REJECTED"

    keyword_match = re.match(r"^\s*(\w+)", statement, flags=re.IGNORECASE)
    if not keyword_match:
        return "INVALID_SQL"

    first_keyword = keyword_match.group(1).upper()
    if first_keyword not in {"SELECT", "WITH"}:
        return "NON_SELECT_REJECTED"

    upper_statement = statement.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_statement):
            return "FORBIDDEN_KEYWORD"

    return None


def _strip_trailing_semicolon(query: str) -> str:
    return re.sub(r";\s*$", "", query).strip()


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def _error_result(error_type: str, message: str, executed_sql: str | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "columns": [],
        "rows": [],
        "row_count": 0,
        "error_type": error_type,
        "message": message,
        "executed_sql": executed_sql,
    }
