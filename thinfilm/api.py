from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from . import config as cfg
from .education import (
    export_report_case_outputs,
    export_report_main_branch_catalog,
    export_report_comparison_figures,
    export_report_chapter2_suite_outputs,
    export_report_main_branch_bundle,
    get_report_main_branch_catalog,
    list_report_chapter2_cases,
    simulate_report_case,
    simulate_report_chapter2_suite,
    simulate_report_design,
)
from .fitting import fit_dual_csv_with_theta2_search_from_files
from .paths import DEG_S_DIR


def fit_two_angle(
    csv_angle1: Path,
    csv_angle2: Path,
    theta1_deg: float,
    theta2_deg: float,
    pol: str = "s",
    use_dispersion: bool = False,
    n1_b: float = 0.0,
    n1_c: float = 0.0,
    n2_b: float = 0.0,
    n2_c: float = 0.0,
    y_selector_angle1: int | str | None = None,
    y_selector_angle2: int | str | None = None,
    save_plots: bool = False,
    sample_id: str = "api_case",
) -> Dict[str, Any]:
    """Run the current two-angle thickness inversion engine."""
    original = {
        "CSV_FILE_ANGLE1": cfg.CSV_FILE_ANGLE1,
        "CSV_FILE_ANGLE2": cfg.CSV_FILE_ANGLE2,
        "THETA1": cfg.THETA1,
        "THETA2": cfg.THETA2,
        "POL": cfg.POL,
        "USE_DISPERSION": cfg.USE_DISPERSION,
        "N1_DISPERSION_B": cfg.N1_DISPERSION_B,
        "N1_DISPERSION_C": cfg.N1_DISPERSION_C,
        "N2_DISPERSION_B": cfg.N2_DISPERSION_B,
        "N2_DISPERSION_C": cfg.N2_DISPERSION_C,
        "FIT_Y_SELECTOR_ANGLE1": cfg.FIT_Y_SELECTOR_ANGLE1,
        "FIT_Y_SELECTOR_ANGLE2": cfg.FIT_Y_SELECTOR_ANGLE2,
    }

    try:
        cfg.CSV_FILE_ANGLE1 = Path(csv_angle1)
        cfg.CSV_FILE_ANGLE2 = Path(csv_angle2)
        cfg.THETA1 = float(theta1_deg)
        cfg.THETA2 = float(theta2_deg)
        cfg.POL = str(pol)
        cfg.USE_DISPERSION = bool(use_dispersion)
        cfg.N1_DISPERSION_B = float(n1_b)
        cfg.N1_DISPERSION_C = float(n1_c)
        cfg.N2_DISPERSION_B = float(n2_b)
        cfg.N2_DISPERSION_C = float(n2_c)
        if y_selector_angle1 is not None:
            cfg.FIT_Y_SELECTOR_ANGLE1 = y_selector_angle1
        if y_selector_angle2 is not None:
            cfg.FIT_Y_SELECTOR_ANGLE2 = y_selector_angle2
        cfg.sync_angle_config_aliases()

        return fit_dual_csv_with_theta2_search_from_files(
            Path(csv_angle1),
            Path(csv_angle2),
            sample_id=sample_id,
            save_plots=save_plots,
        )
    finally:
        for name, value in original.items():
            setattr(cfg, name, value)
        cfg.sync_angle_config_aliases()


def fit_current_main_case(save_plots: bool = False) -> Dict[str, Any]:
    """Run the current recommended 60 nm, 10deg + 80deg, s-polarized case."""
    return fit_two_angle(
        csv_angle1=DEG_S_DIR / "60nm_10deg_s.csv",
        csv_angle2=DEG_S_DIR / "60nm_80deg_s.csv",
        theta1_deg=10.0,
        theta2_deg=80.0,
        pol="s",
        use_dispersion=False,
        save_plots=save_plots,
        sample_id="current_main_case",
    )


def simulate_teaching_design(
    design_type: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """APP-facing wrapper for the report-style forward thin-film simulator."""
    return simulate_report_design(design_type=design_type, **kwargs)


def list_teaching_cases() -> list[dict[str, Any]]:
    """APP-facing chapter-2 case catalog."""
    return list_report_chapter2_cases()


def get_teaching_main_branch_catalog() -> Dict[str, Any]:
    """APP-facing UI catalog for the whole teaching main branch."""
    return get_report_main_branch_catalog()


def simulate_teaching_case(
    case_id: str,
    **kwargs: Any,
) -> Dict[str, Any]:
    """APP-facing wrapper for one chapter-2 preset case."""
    return simulate_report_case(case_id=case_id, **kwargs)


def simulate_teaching_suite(
    **kwargs: Any,
) -> Dict[str, Dict[str, Any]]:
    """APP-facing wrapper for the full chapter-2 preset suite."""
    return simulate_report_chapter2_suite(**kwargs)


def export_teaching_case_outputs(
    case_id: str,
    **kwargs: Any,
) -> Dict[str, str]:
    """Run one teaching case and export plot/data/report files."""
    export_keys = {"prefix", "save_plot", "save_csv", "save_json", "save_txt"}
    export_kwargs = {key: kwargs.pop(key) for key in list(kwargs.keys()) if key in export_keys}
    result = simulate_report_case(case_id=case_id, **kwargs)
    return export_report_case_outputs(result=result, **export_kwargs)


def export_teaching_suite_outputs(
    **kwargs: Any,
) -> Dict[str, Dict[str, str]]:
    """Run and export the whole chapter-2 teaching suite."""
    return export_report_chapter2_suite_outputs(**kwargs)


def export_teaching_comparison_figures(
    **kwargs: Any,
) -> Dict[str, Dict[str, str]]:
    """Export report-style multi-curve comparison figures for the main teaching branch."""
    return export_report_comparison_figures(**kwargs)


def export_teaching_main_branch_catalog(
    **kwargs: Any,
) -> Dict[str, Any]:
    """Export the UI-friendly main-branch catalog to JSON."""
    return export_report_main_branch_catalog(**kwargs)


def export_teaching_report_bundle(
    **kwargs: Any,
) -> Dict[str, Any]:
    """Export the whole main teaching branch as a report-style bundle."""
    return export_report_main_branch_bundle(**kwargs)
