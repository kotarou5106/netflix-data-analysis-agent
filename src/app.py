import sys

from src.graph import run_agent


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python3 -m src.app "问题"')
        return

    user_query = " ".join(sys.argv[1:]).strip()
    if not user_query:
        print('Usage: python3 -m src.app "问题"')
        return

    state = run_agent(user_query)
    print(state.final_report)

    if state.errors:
        print("\n## Errors / 错误信息")
        for error in state.errors:
            print(f"- {error}")


if __name__ == "__main__":
    main()
