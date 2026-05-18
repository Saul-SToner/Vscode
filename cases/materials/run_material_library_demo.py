from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from thinfilm import (
    export_real_material_library_outputs,
    export_report_case_outputs,
    simulate_teaching_design,
    simulate_teaching_design_real_materials,
)
from thinfilm.paths import output_file


DEMO_CASES: dict[str, dict[str, Any]] = {
    "single_ar": {
        "design_type": "single_ar",
        "title": "single_ar_MgF2_on_SiO2",
        "material_map": {
            "n_incident": "Air",
            "n_low": "MgF2",
            "n_substrate": "SiO2",
        },
        "kwargs": {
            "lambda0_nm": 550.0,
            "wavelengths_nm": list(range(430, 751, 2)),
        },
    },
    "bragg_reflector": {
        "design_type": "bragg_reflector",
        "title": "bragg_SiO2_TiO2",
        "material_map": {
            "n_incident": "Air",
            "n_low": "SiO2",
            "n_high_2": "TiO2",
            "n_substrate": "SiO2",
        },
        "kwargs": {
            "lambda0_nm": 550.0,
            "periods": 6,
            "wavelengths_nm": list(range(430, 751, 2)),
        },
    },
    "fp_filter": {
        "design_type": "fp_filter",
        "title": "fp_filter_SiO2_TiO2",
        "material_map": {
            "n_incident": "Air",
            "n_low": "SiO2",
            "n_high_2": "TiO2",
            "n_substrate": "SiO2",
        },
        "kwargs": {
            "lambda0_nm": 550.0,
            "periods": 3,
            "wavelengths_nm": list(range(430, 751, 2)),
        },
    },
}


def _comparison_rows(constant: dict[str, Any], real: dict[str, Any]) -> list[dict[str, float]]:
    wavelengths = real["wavelength_nm"]
    rows: list[dict[str, float]] = []
    for idx, wl in enumerate(wavelengths):
        rows.append(
            {
                "wavelength_nm": float(wl),
                "R_constant": float(constant["R"][idx]),
                "T_constant": float(constant["T"][idx]),
                "A_constant": float(constant["A"][idx]),
                "R_real_nk": float(real["R"][idx]),
                "T_real_nk": float(real["T"][idx]),
                "A_real_nk": float(real["A"][idx]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Export real-material-library demo files.")
    parser.add_argument("--prefix", default="real_material_library_demo")
    parser.add_argument(
        "--case",
        action="append",
        choices=sorted(DEMO_CASES),
        help="Demo case to export. Can be repeated. Default: all cases.",
    )
    args = parser.parse_args()

    material_files = export_real_material_library_outputs(prefix=args.prefix)
    selected = args.case or list(DEMO_CASES)
    case_outputs: dict[str, Any] = {}

    for case_id in selected:
        spec = DEMO_CASES[case_id]
        kwargs = dict(spec["kwargs"])
        material_map = dict(spec["material_map"])
        constant = simulate_teaching_design(spec["design_type"], **kwargs)
        real = simulate_teaching_design_real_materials(
            spec["design_type"],
            material_map=material_map,
            **kwargs,
        )
        constant["case_id"] = f"{case_id}_constant"
        real["case_id"] = f"{case_id}_real_nk"
        const_files = export_report_case_outputs(
            constant,
            prefix=f"{args.prefix}_{case_id}_constant",
        )
        real_files = export_report_case_outputs(
            real,
            prefix=f"{args.prefix}_{case_id}_real_nk",
        )

        comparison_csv = output_file(f"{args.prefix}_{case_id}_constant_vs_real_nk.csv")
        rows = _comparison_rows(constant, real)
        with comparison_csv.open("w", encoding="utf-8") as f:
            f.write("wavelength_nm,R_constant,T_constant,A_constant,R_real_nk,T_real_nk,A_real_nk\n")
            for row in rows:
                f.write(
                    f"{row['wavelength_nm']:.12g},{row['R_constant']:.12g},{row['T_constant']:.12g},"
                    f"{row['A_constant']:.12g},{row['R_real_nk']:.12g},{row['T_real_nk']:.12g},"
                    f"{row['A_real_nk']:.12g}\n"
                )

        case_outputs[case_id] = {
            "constant_files": const_files,
            "real_nk_files": real_files,
            "comparison_csv": str(comparison_csv),
            "material_map": material_map,
            "real_summary": real["summary"],
        }

    manifest = {
        "material_library": material_files,
        "cases": case_outputs,
    }
    manifest_path = output_file(f"{args.prefix}_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("真实材料库演示包已导出")
    print(f"manifest = {manifest_path}")
    print(f"overview  = {material_files['overview_png']}")


if __name__ == "__main__":
    main()
