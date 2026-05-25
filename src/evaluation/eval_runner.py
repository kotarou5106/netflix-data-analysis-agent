import argparse
import json
import time
from pathlib import Path

from src.evaluation.metrics import (
    intent_match,
    section_completeness_score,
    tool_selection_score,
)
from src.graph import run_agent


DEFAULT_LIMIT = 3
TEST_CASES_PATH = Path(__file__).resolve().parents[2] / "eval" / "test_cases.json"


def load_test_cases(path: Path = TEST_CASES_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_evaluation(limit: int = DEFAULT_LIMIT, run_all: bool = False, agent_runner=run_agent) -> dict:
    test_cases = load_test_cases()
    selected_cases = test_cases if run_all else test_cases[:limit]

    total_start = time.perf_counter()
    results = []

    for index, test_case in enumerate(selected_cases, start=1):
        case_start = time.perf_counter()
        state = agent_runner(test_case["question"])
        elapsed = time.perf_counter() - case_start

        result = {
            "question": test_case["question"],
            "intent_match": intent_match(state.intent, test_case["expected_intent"]),
            "tool_selection_score": tool_selection_score(
                state.selected_tools,
                test_case["expected_tools"],
            ),
            "section_completeness_score": section_completeness_score(
                state.final_report,
                test_case["required_sections"],
            ),
            "time_seconds": elapsed,
        }
        results.append(result)
        print(f"case {index}: {elapsed:.2f}s - {test_case['question']}")

    total_cases = len(results)
    total_time_seconds = time.perf_counter() - total_start

    summary = {
        "total_cases": total_cases,
        "intent_accuracy": _average(1.0 if item["intent_match"] else 0.0 for item in results),
        "avg_tool_selection_score": _average(item["tool_selection_score"] for item in results),
        "avg_section_completeness_score": _average(
            item["section_completeness_score"] for item in results
        ),
        "total_time_seconds": total_time_seconds,
    }

    _print_summary(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Netflix Agent evaluation cases.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    run_evaluation(limit=args.limit, run_all=args.all)


def _average(values) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _print_summary(summary: dict) -> None:
    print("Evaluation Summary")
    print(f"total_cases: {summary['total_cases']}")
    print(f"intent_accuracy: {summary['intent_accuracy']:.4f}")
    print(f"avg_tool_selection_score: {summary['avg_tool_selection_score']:.4f}")
    print(f"avg_section_completeness_score: {summary['avg_section_completeness_score']:.4f}")
    print(f"total_time_seconds: {summary['total_time_seconds']:.2f}")


if __name__ == "__main__":
    main()
