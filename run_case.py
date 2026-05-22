from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


CASE_SCRIPTS: dict[str, dict[str, str]] = {
    "absorbing_surface": {
        "baseline_template": "cases/absorbing_surface/run_absorbing_surface_baseline_template.py",
        "bundle": "cases/absorbing_surface/run_absorbing_surface_bundle.py",
        "gain": "cases/absorbing_surface/run_absorbing_surface_gain.py",
        "gain_trend": "cases/absorbing_surface/run_absorbing_surface_gain_trend.py",
        "topic_bundle": "cases/absorbing_surface/run_absorbing_surface_topic_bundle.py",
    },
    "advanced_ar": {
        "bundle": "cases/advanced_ar/run_advanced_ar_bundle.py",
        "porous_double_ar": "cases/advanced_ar/run_porous_double_ar_topic_bundle.py",
        "porous_double_ar_topic_bundle": "cases/advanced_ar/run_porous_double_ar_topic_bundle.py",
        "rugate_80layer": "cases/advanced_ar/run_rugate_80layer_table.py",
        "rugate_80layer_table": "cases/advanced_ar/run_rugate_80layer_table.py",
    },
    "frontier": {
        "model_tree": "cases/frontier/run_frontier_model_tree.py",
    },
    "guided_grating": {
        "demo": "cases/guided_grating/run_guided_grating_demo.py",
    },
    "materials": {
        "demo": "cases/materials/run_material_library_demo.py",
    },
    "pdrc": {
        "cooling_bundle": "cases/pdrc/run_pdrc_cooling_bundle.py",
    },
    "tamm": {
        "interface_priority": "cases/tamm/run_tamm_interface_priority.py",
        "interface_window_bundle": "cases/tamm/run_tamm_interface_window_bundle.py",
        "interface_window_scan": "cases/tamm/run_tamm_interface_window_scan.py",
        "phase_bundle": "cases/tamm/run_tamm_phase_bundle.py",
        "phase_candidates": "cases/tamm/run_tamm_phase_candidates.py",
        "phase_focus": "cases/tamm/run_tamm_phase_focus.py",
        "reflection_phase_screen": "cases/tamm/run_tamm_reflection_phase_screen.py",
    },
    "teaching": {
        "demo": "cases/teaching/run_teaching_demo.py",
        "expansion_validation": "cases/teaching/run_teaching_expansion_validation.py",
        "metrics_bundle": "cases/teaching/run_teaching_metrics_bundle.py",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified entry point for non-public case scripts under cases/*/.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_case.py --group tamm --case phase_bundle -- --csv path/to/scan.csv\n"
            "  python run_case.py --group pdrc --case cooling_bundle -- --comsol-csv path/to/pdrc.csv\n"
            "  python run_case.py --group advanced_ar --case bundle -- --single-ar-csv path/to/single.csv\n"
        ),
    )
    parser.add_argument("--group", choices=sorted(CASE_SCRIPTS))
    parser.add_argument("--case", help="Case key within the selected group.")
    parser.add_argument("--list", action="store_true", help="List available groups and cases.")
    return parser


def print_cases() -> None:
    print("Available case scripts:")
    for group, cases in sorted(CASE_SCRIPTS.items()):
        print(f"  [{group}]")
        for case, script in sorted(cases.items()):
            print(f"    {case:<30} -> {script}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args, passthrough = parser.parse_known_args(argv)

    if args.list:
        print_cases()
        return

    if not args.group or not args.case:
        parser.error("--group and --case are required unless --list is used")

    group_cases = CASE_SCRIPTS[args.group]
    if args.case not in group_cases:
        known = ", ".join(sorted(group_cases))
        raise SystemExit(f"Unknown case '{args.case}' for group '{args.group}'. Available: {known}")

    script = ROOT / group_cases[args.case]
    if not script.exists():
        raise SystemExit(f"Case script not found: {script}")

    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    sys.path.insert(0, str(ROOT))
    sys.argv = [str(script), *passthrough]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
