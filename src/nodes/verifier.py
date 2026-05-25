from src.state import AgentState


REQUIRED_SECTIONS = {
    "Evidence / 证据": "Missing required section: Evidence / 证据",
    "Limitations / 限制说明": "Missing required section: Limitations / 限制说明",
}

CAUSAL_REPLACEMENTS = {
    "导致": "可能相关",
    "证明": "显示出相关迹象",
    "必然": "可能",
    "cause": "be associated with",
    "prove": "suggest",
    "necessarily": "possibly",
}


def verify_report(state: AgentState) -> AgentState:
    report = state.draft_report
    issues = []

    for section, message in REQUIRED_SECTIONS.items():
        if section not in report:
            issues.append(message)

    revised_report = report
    for phrase, replacement in CAUSAL_REPLACEMENTS.items():
        if phrase in revised_report:
            issues.append(f"Strong causal expression found: {phrase}")
            revised_report = revised_report.replace(phrase, replacement)

    revised = revised_report != report
    passed = not issues

    state.verification_result = {
        "passed": passed,
        "issues": issues,
        "revised": revised,
    }
    state.final_report = revised_report if issues else report

    return state
