from __future__ import annotations

from pprint import pprint

from guided_grating import run_minimal_demo


def main() -> None:
    result = run_minimal_demo()
    print("已导出光栅波导支线最小示例。")
    print(f"  warning: {result['warning']}")
    print("  summary:")
    pprint(result["summary"])
    print("  files:")
    for key, value in result["files"].items():
        print(f"    {key}: {value}")


if __name__ == "__main__":
    main()
