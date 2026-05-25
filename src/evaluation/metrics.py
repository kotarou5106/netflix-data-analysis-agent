def intent_match(predicted, expected) -> bool:
    return predicted == expected


def tool_selection_score(predicted_tools, expected_tools) -> float:
    if not expected_tools:
        return 1.0

    predicted_set = set(predicted_tools or [])
    expected_set = set(expected_tools)
    return len(predicted_set & expected_set) / len(expected_set)


def section_completeness_score(report, required_sections) -> float:
    if not required_sections:
        return 1.0

    report_text = report or ""
    matched_sections = sum(1 for section in required_sections if section in report_text)
    return matched_sections / len(required_sections)
