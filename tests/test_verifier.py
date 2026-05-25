from src.nodes.verifier import verify_report
from src.state import AgentState


VALID_REPORT = """
# Analysis Report / 分析报告

## Evidence / 证据

- 数据显示该群体风险更高。

## Limitations / 限制说明

- 本报告只支持观察性分析。
"""


def test_missing_limitations_is_detected():
    state = AgentState(
        draft_report="""
        # Analysis Report / 分析报告

        ## Evidence / 证据

        - 有数据证据。
        """
    )

    verified = verify_report(state)

    assert verified.verification_result["passed"] is False
    assert any("Limitations / 限制说明" in issue for issue in verified.verification_result["issues"])


def test_missing_evidence_is_detected():
    state = AgentState(
        draft_report="""
        # Analysis Report / 分析报告

        ## Limitations / 限制说明

        - 只支持观察性分析。
        """
    )

    verified = verify_report(state)

    assert verified.verification_result["passed"] is False
    assert any("Evidence / 证据" in issue for issue in verified.verification_result["issues"])


def test_strong_causal_expression_is_revised():
    state = AgentState(
        draft_report="""
        # Analysis Report / 分析报告

        ## Evidence / 证据

        - 推荐点击率低导致流失。

        ## Limitations / 限制说明

        - 本报告只支持观察性分析。
        """
    )

    verified = verify_report(state)

    assert verified.verification_result["passed"] is False
    assert verified.verification_result["revised"] is True
    assert "推荐点击率低可能相关流失" in verified.final_report
    assert "导致" not in verified.final_report


def test_valid_report_passes():
    state = AgentState(draft_report=VALID_REPORT)

    verified = verify_report(state)

    assert verified.verification_result["passed"] is True
    assert verified.verification_result["issues"] == []
    assert verified.verification_result["revised"] is False


def test_verifier_writes_final_report():
    state = AgentState(draft_report=VALID_REPORT)

    verified = verify_report(state)

    assert verified.final_report == VALID_REPORT
