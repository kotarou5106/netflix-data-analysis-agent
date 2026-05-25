from src.evaluation.metrics import (
    intent_match,
    section_completeness_score,
    tool_selection_score,
)


def test_intent_match():
    assert intent_match("churn_analysis", "churn_analysis") is True
    assert intent_match("general_analysis", "churn_analysis") is False


def test_tool_selection_score():
    score = tool_selection_score(
        ["rag_search", "sql_query", "report_writer"],
        ["rag_search", "sql_query", "python_analysis"],
    )

    assert score == 2 / 3


def test_section_completeness_score():
    report = """
    ## Evidence / 证据
    ## Key Findings / 关键发现
    """

    score = section_completeness_score(
        report,
        ["Evidence / 证据", "Key Findings / 关键发现", "Limitations / 限制说明"],
    )

    assert score == 2 / 3
