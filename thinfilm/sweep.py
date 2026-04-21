from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

import thinfilm_core as core

from .paths import DEG_P_DIR, output_file


def summarize_n1b_theta_sweep(
    csv_path: Path | None = None,
    output_name: str = "n1b_theta_sweep_summary.csv",
) -> pd.DataFrame:
    """Summarize a COMSOL full-combination sweep table grouped by theta and n1_B."""
    path = DEG_P_DIR / "p.csv" if csv_path is None else Path(csv_path)
    spec = core.load_spectrum_csv(path, y_selector=5)
    df = spec.data_table.copy()

    wavelength_nm = df.iloc[:, 0].to_numpy(dtype=float) * 1e9
    theta_deg = df.iloc[:, 1].to_numpy(dtype=float)
    n1_b = df.iloc[:, 2].to_numpy(dtype=float)
    reflectance = df.iloc[:, 5].to_numpy(dtype=float)

    rows: List[Dict[str, float]] = []
    for theta_value in sorted(np.unique(theta_deg)):
        theta_mask = np.isclose(theta_deg, theta_value)
        base_curve = None

        for b_value in sorted(np.unique(n1_b[theta_mask])):
            mask = theta_mask & np.isclose(n1_b, b_value)
            order = np.argsort(wavelength_nm[mask])
            curve = reflectance[mask][order]
            wl = wavelength_nm[mask][order]

            if base_curve is None:
                rmse_vs_b0 = 0.0
                maxabs_vs_b0 = 0.0
                base_curve = curve
            else:
                diff = curve - base_curve
                rmse_vs_b0 = float(np.sqrt(np.mean(diff ** 2)))
                maxabs_vs_b0 = float(np.max(np.abs(diff)))

            rows.append(
                {
                    "theta_deg": float(theta_value),
                    "n1_B": float(b_value),
                    "n_points": int(len(curve)),
                    "lambda_min_nm": float(np.min(wl)),
                    "lambda_max_nm": float(np.max(wl)),
                    "reflectance_mean": float(np.mean(curve)),
                    "reflectance_min": float(np.min(curve)),
                    "reflectance_max": float(np.max(curve)),
                    "rmse_vs_n1_B_0": rmse_vs_b0,
                    "maxabs_vs_n1_B_0": maxabs_vs_b0,
                }
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return summary
