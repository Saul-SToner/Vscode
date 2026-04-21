from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import thinfilm_core as core

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
    save_plots: bool = False,
    sample_id: str = "api_case",
) -> Dict[str, Any]:
    """Run the current two-angle thickness inversion engine."""
    original = {
        "CSV_FILE_ANGLE1": core.CSV_FILE_ANGLE1,
        "CSV_FILE_ANGLE2": core.CSV_FILE_ANGLE2,
        "THETA1": core.THETA1,
        "THETA2": core.THETA2,
        "POL": core.POL,
        "USE_DISPERSION": core.USE_DISPERSION,
        "N1_DISPERSION_B": core.N1_DISPERSION_B,
        "N1_DISPERSION_C": core.N1_DISPERSION_C,
        "N2_DISPERSION_B": core.N2_DISPERSION_B,
        "N2_DISPERSION_C": core.N2_DISPERSION_C,
    }

    try:
        core.CSV_FILE_ANGLE1 = Path(csv_angle1)
        core.CSV_FILE_ANGLE2 = Path(csv_angle2)
        core.THETA1 = float(theta1_deg)
        core.THETA2 = float(theta2_deg)
        core.POL = str(pol)
        core.USE_DISPERSION = bool(use_dispersion)
        core.N1_DISPERSION_B = float(n1_b)
        core.N1_DISPERSION_C = float(n1_c)
        core.N2_DISPERSION_B = float(n2_b)
        core.N2_DISPERSION_C = float(n2_c)
        core.sync_angle_config_aliases()

        return core.fit_dual_csv_with_theta2_search_from_files(
            Path(csv_angle1),
            Path(csv_angle2),
            sample_id=sample_id,
            save_plots=save_plots,
        )
    finally:
        for name, value in original.items():
            setattr(core, name, value)
        core.sync_angle_config_aliases()


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
