from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .api import fit_two_angle
from . import config as cfg
from .fitting import evaluate_dual_fit_objective, multiscale_dual_search
from .io import load_spectrum_csv
from .objectives import evaluate_curve_objective, smooth_signal_1d, standardize_signal
from .optics import unify_two_reflectance_curves
from .paths import DEG_P_DIR, output_file


def _theta_column_to_deg(theta_values: np.ndarray) -> np.ndarray:
    theta_values = np.asarray(theta_values, dtype=float)
    finite = theta_values[np.isfinite(theta_values)]
    if len(finite) > 0 and np.nanmax(np.abs(finite)) <= 2.5 * np.pi:
        return np.rad2deg(theta_values)
    return theta_values


def summarize_n1b_theta_sweep(
    csv_path: Path | None = None,
    reflectance_scale: float = 1.0,
    output_name: str = "n1b_theta_sweep_summary.csv",
) -> pd.DataFrame:
    """Summarize a COMSOL full-combination sweep table grouped by theta and n1_B."""
    path = DEG_P_DIR / "p.csv" if csv_path is None else Path(csv_path)
    spec = load_spectrum_csv(path, y_selector=5)
    df = spec.data_table.copy()

    wavelength_nm = df.iloc[:, 0].to_numpy(dtype=float) * 1e9
    theta_deg = _theta_column_to_deg(df.iloc[:, 1].to_numpy(dtype=float))
    n1_b = df.iloc[:, 2].to_numpy(dtype=float)
    reflectance = df.iloc[:, 5].to_numpy(dtype=float) * float(reflectance_scale)

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
                    "reflectance_scale": float(reflectance_scale),
                    "rmse_vs_n1_B_0": rmse_vs_b0,
                    "maxabs_vs_n1_B_0": maxabs_vs_b0,
                }
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return summary


def _extract_curve_from_sweep_table(
    df: pd.DataFrame,
    theta_deg: float,
    n1_b: float,
    reflectance_scale: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    wavelength_nm = df.iloc[:, 0].to_numpy(dtype=float) * 1e9
    theta_values = _theta_column_to_deg(df.iloc[:, 1].to_numpy(dtype=float))
    n1_b_values = df.iloc[:, 2].to_numpy(dtype=float)
    reflectance = df.iloc[:, 5].to_numpy(dtype=float) * float(reflectance_scale)

    mask = np.isclose(theta_values, theta_deg) & np.isclose(n1_b_values, n1_b)
    if not np.any(mask):
        raise ValueError(f"No curve found for theta={theta_deg}, n1_B={n1_b}.")

    order = np.argsort(wavelength_nm[mask])
    return wavelength_nm[mask][order], reflectance[mask][order]


def _write_curve_csv(path: Path, wavelength_nm: np.ndarray, reflectance: np.ndarray, theta_deg: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(
        {
            "wavelength_nm": wavelength_nm,
            "reflectance": reflectance,
            "theta_deg": np.full_like(wavelength_nm, float(theta_deg), dtype=float),
        }
    )
    out.to_csv(path, index=False, encoding="utf-8-sig")


def _cauchy_index_profile(
    lam: np.ndarray,
    n_a: float,
    n_b: float,
    n_c: float,
) -> np.ndarray:
    lam = np.asarray(lam, dtype=float)
    lam_um = np.clip(lam * 1e6, 1e-9, None)
    return float(n_a) + float(n_b) / (lam_um ** 2) + float(n_c) / (lam_um ** 4)


def _thinfilm_reflectance_angle_local(
    lam: np.ndarray,
    d: float,
    theta0_deg: float,
    pol: str,
    n0: float,
    n1_a: float,
    n1_b: float,
    n1_c: float,
    n2_a: float,
    n2_b: float,
    n2_c: float,
    mix_p_weight: float = 0.5,
) -> np.ndarray:
    """Forward model used by sweep screens; avoids global dispersion state."""
    lam = np.asarray(lam, dtype=float)
    theta0 = np.deg2rad(theta0_deg)
    n0_arr = np.full_like(lam, float(n0), dtype=float)
    n1_arr = _cauchy_index_profile(lam, n1_a, n1_b, n1_c)
    n2_arr = _cauchy_index_profile(lam, n2_a, n2_b, n2_c)

    sin_theta1 = np.clip(n0_arr * np.sin(theta0) / n1_arr, -1.0, 1.0)
    sin_theta2 = np.clip(n0_arr * np.sin(theta0) / n2_arr, -1.0, 1.0)
    theta1 = np.arcsin(sin_theta1)
    theta2 = np.arcsin(sin_theta2)

    c0 = np.cos(theta0)
    c1 = np.cos(theta1)
    c2 = np.cos(theta2)
    beta = 2.0 * np.pi * n1_arr * float(d) * c1 / lam

    r01_s = (n0_arr * c0 - n1_arr * c1) / (n0_arr * c0 + n1_arr * c1)
    r12_s = (n1_arr * c1 - n2_arr * c2) / (n1_arr * c1 + n2_arr * c2)
    phase = np.exp(2j * beta)
    r_s = (r01_s + r12_s * phase) / (1.0 + r01_s * r12_s * phase)
    r_s_power = np.abs(r_s) ** 2

    r01_p = (n1_arr * c0 - n0_arr * c1) / (n1_arr * c0 + n0_arr * c1)
    r12_p = (n2_arr * c1 - n1_arr * c2) / (n2_arr * c1 + n1_arr * c2)
    r_p = (r01_p + r12_p * phase) / (1.0 + r01_p * r12_p * phase)
    r_p_power = np.abs(r_p) ** 2

    pol_key = str(pol).strip().lower()
    if pol_key == "s":
        return r_s_power
    if pol_key == "p":
        return r_p_power
    if pol_key == "avg":
        return 0.5 * (r_s_power + r_p_power)
    if pol_key == "mix":
        eta = float(np.clip(mix_p_weight, 0.0, 1.0))
        return eta * r_p_power + (1.0 - eta) * r_s_power
    raise ValueError("pol must be 's', 'p', 'avg', or 'mix'.")


def _evaluate_dual_fit_objective_local(
    lam: np.ndarray,
    r1: np.ndarray,
    theta1_deg: float,
    r2: np.ndarray,
    theta2_deg: float,
    d: float,
    pol: str,
    n0: float,
    n1_a: float,
    n1_b: float,
    n1_c: float,
    n2_a: float,
    n2_b: float,
    n2_c: float,
) -> float:
    rm1 = _thinfilm_reflectance_angle_local(
        lam, d, theta1_deg, pol, n0, n1_a, n1_b, n1_c, n2_a, n2_b, n2_c, cfg.MIX_P_WEIGHT
    )
    rm2 = _thinfilm_reflectance_angle_local(
        lam, d, theta2_deg, pol, n0, n1_a, n1_b, n1_c, n2_a, n2_b, n2_c, cfg.MIX_P_WEIGHT
    )

    err1, (a1, b1), _ = evaluate_curve_objective(
        lam=lam,
        y_obs=r1,
        y_model=rm1,
        lambda_a=cfg.LAMBDA_A,
        lambda_b=cfg.LAMBDA_B,
        smooth_window=cfg.OBJECTIVE_SMOOTH_WINDOW,
        weight_level=cfg.OBJECTIVE_WEIGHT_LEVEL,
        weight_shape=cfg.OBJECTIVE_WEIGHT_SHAPE,
        weight_slope=cfg.OBJECTIVE_WEIGHT_SLOPE,
    )
    err2, (a2, b2), _ = evaluate_curve_objective(
        lam=lam,
        y_obs=r2,
        y_model=rm2,
        lambda_a=cfg.LAMBDA_A,
        lambda_b=cfg.LAMBDA_B,
        smooth_window=cfg.OBJECTIVE_SMOOTH_WINDOW,
        weight_level=cfg.OBJECTIVE_WEIGHT_LEVEL,
        weight_shape=cfg.OBJECTIVE_WEIGHT_SHAPE,
        weight_slope=cfg.OBJECTIVE_WEIGHT_SLOPE,
    )

    lam_span = max(float(np.max(lam) - np.min(lam)), 1e-18)
    lam_norm = (lam - np.mean(lam)) / lam_span
    rm1_adj = rm1 + a1 + b1 * lam_norm
    rm2_adj = rm2 + a2 + b2 * lam_norm

    delta_obs = smooth_signal_1d(r2 - r1, window=cfg.OBJECTIVE_SMOOTH_WINDOW)
    delta_model = smooth_signal_1d(rm2_adj - rm1_adj, window=cfg.OBJECTIVE_SMOOTH_WINDOW)
    delta_shape_err = float(np.mean((standardize_signal(delta_obs) - standardize_signal(delta_model)) ** 2))
    delta_slope_err = float(
        np.mean(
            (
                standardize_signal(np.gradient(delta_obs, lam_norm))
                - standardize_signal(np.gradient(delta_model, lam_norm))
            )
            ** 2
        )
    )
    common_err = float(0.5 * (err1 + err2))
    delta_err = float(0.35 * delta_shape_err + 0.65 * delta_slope_err)
    return float(0.55 * common_err + 0.45 * delta_err)


def _material_params_from_d_n1b_group(
    df: pd.DataFrame,
    thickness_m: float,
    n1_b: float,
) -> Dict[str, float]:
    params = {
        "n1_A": float(cfg.N1),
        "n1_B": float(n1_b),
        "n1_C": 0.0,
        "n2_A": float(cfg.N2),
        "n2_B": 0.0,
        "n2_C": 0.0,
    }
    if df.shape[1] < 14:
        return params

    thickness_values = df.iloc[:, 2].to_numpy(dtype=float)
    n1_b_values = df.iloc[:, 3].to_numpy(dtype=float)
    mask = np.isclose(thickness_values, thickness_m) & np.isclose(n1_b_values, n1_b)
    if not np.any(mask):
        return params

    for key, col_idx in (
        ("n1_A", 8),
        ("n1_C", 10),
        ("n2_A", 11),
        ("n2_B", 12),
        ("n2_C", 13),
    ):
        values = df.iloc[:, col_idx].to_numpy(dtype=float)[mask]
        finite = values[np.isfinite(values)]
        if len(finite) > 0:
            params[key] = float(np.median(finite))
    return params


def screen_d_n1b_sweep_quality(
    csv_path: Path | None = None,
    pol: str = "p",
    reflectance_scale: float = 1.0,
    max_reflectance_threshold: float = 0.7,
    max_jump_threshold: float = 0.08,
    roughness_threshold: float = 0.08,
    output_name: str = "d_n1b_theta_sweep_quality_screen.csv",
) -> pd.DataFrame:
    """Screen COMSOL d+n1_B sweep curves before expensive inverse fitting."""
    path = DEG_P_DIR / "d_p.csv" if csv_path is None else Path(csv_path)
    spec = load_spectrum_csv(path, y_selector=6)
    df = spec.data_table.copy()

    wavelength_nm = df.iloc[:, 0].to_numpy(dtype=float) * 1e9
    theta_values = _theta_column_to_deg(df.iloc[:, 1].to_numpy(dtype=float))
    thickness_values_nm = df.iloc[:, 2].to_numpy(dtype=float) * 1e9
    n1_b_values = df.iloc[:, 3].to_numpy(dtype=float)
    reflectance = df.iloc[:, 6].to_numpy(dtype=float) * float(reflectance_scale)

    rows: List[Dict[str, float | bool]] = []
    for thickness_nm in sorted(np.unique(thickness_values_nm)):
        thickness_m = float(thickness_nm) * 1e-9
        for theta_deg in sorted(np.unique(theta_values)):
            for n1_b in sorted(np.unique(n1_b_values)):
                mask = (
                    np.isclose(thickness_values_nm, thickness_nm)
                    & np.isclose(theta_values, theta_deg)
                    & np.isclose(n1_b_values, n1_b)
                )
                if not np.any(mask):
                    continue

                order = np.argsort(wavelength_nm[mask])
                wl_nm = wavelength_nm[mask][order]
                y_obs = reflectance[mask][order]
                jumps = np.abs(np.diff(y_obs))
                roughness = (
                    float(np.sqrt(np.mean(np.diff(y_obs, n=2) ** 2)))
                    if len(y_obs) > 2
                    else 0.0
                )

                material = _material_params_from_d_n1b_group(df, thickness_m, float(n1_b))
                y_model = _thinfilm_reflectance_angle_local(
                    wl_nm * 1e-9,
                    thickness_m,
                    float(theta_deg),
                    pol,
                    cfg.N0,
                    material["n1_A"],
                    material["n1_B"],
                    material["n1_C"],
                    material["n2_A"],
                    material["n2_B"],
                    material["n2_C"],
                    cfg.MIX_P_WEIGHT,
                )
                model_rmse = float(np.sqrt(np.mean((y_obs - y_model) ** 2)))
                model_max_abs = float(np.max(np.abs(y_obs - y_model)))

                max_reflectance = float(np.max(y_obs))
                max_jump = float(np.max(jumps)) if len(jumps) else 0.0
                pass_quality = bool(
                    max_reflectance <= float(max_reflectance_threshold)
                    and max_jump <= float(max_jump_threshold)
                    and roughness <= float(roughness_threshold)
                )

                rows.append(
                    {
                        "true_thickness_nm": float(thickness_nm),
                        "theta_deg": float(theta_deg),
                        "n1_B": float(n1_b),
                        "n_points": int(len(y_obs)),
                        "lambda_min_nm": float(np.min(wl_nm)),
                        "lambda_max_nm": float(np.max(wl_nm)),
                        "reflectance_min": float(np.min(y_obs)),
                        "reflectance_mean": float(np.mean(y_obs)),
                        "reflectance_max": max_reflectance,
                        "max_adjacent_jump": max_jump,
                        "roughness_second_diff": roughness,
                        "model_rmse_at_nominal": model_rmse,
                        "model_max_abs_at_nominal": model_max_abs,
                        "passes_quality": pass_quality,
                    }
                )

    quality_df = pd.DataFrame(rows)
    quality_df = quality_df.sort_values(
        [
            "passes_quality",
            "true_thickness_nm",
            "theta_deg",
            "model_rmse_at_nominal",
            "max_adjacent_jump",
        ],
        ascending=[False, True, True, True, True],
    ).reset_index(drop=True)
    quality_df.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return quality_df


def fit_n1b_theta_sweep(
    csv_path: Path | None = None,
    theta1_deg: float = 10.0,
    theta2_deg: float = 80.0,
    pol: str = "p",
    reflectance_scale: float = 1.0,
    output_name: str = "n1b_theta_sweep_fit_results.csv",
) -> pd.DataFrame:
    """Fit each n1_B group in a COMSOL theta+n1_B+lambda sweep table."""
    path = DEG_P_DIR / "p.csv" if csv_path is None else Path(csv_path)
    spec = load_spectrum_csv(path, y_selector=5)
    df = spec.data_table.copy()
    n1_b_values = sorted(np.unique(df.iloc[:, 2].to_numpy(dtype=float)))

    temp_dir = output_file("_sweep_temp").parent / "_sweep_temp"
    rows: List[Dict[str, float]] = []

    for n1_b in n1_b_values:
        w1_nm, r1 = _extract_curve_from_sweep_table(df, theta1_deg, float(n1_b), reflectance_scale)
        w2_nm, r2 = _extract_curve_from_sweep_table(df, theta2_deg, float(n1_b), reflectance_scale)

        file1 = temp_dir / f"theta{theta1_deg:g}_n1B_{n1_b:.6f}.csv"
        file2 = temp_dir / f"theta{theta2_deg:g}_n1B_{n1_b:.6f}.csv"
        _write_curve_csv(file1, w1_nm, r1, theta1_deg)
        _write_curve_csv(file2, w2_nm, r2, theta2_deg)

        result = fit_two_angle(
            csv_angle1=file1,
            csv_angle2=file2,
            theta1_deg=theta1_deg,
            theta2_deg=theta2_deg,
            pol=pol,
            use_dispersion=True,
            n1_b=float(n1_b),
            n1_c=0.0,
            n2_b=0.0,
            n2_c=0.0,
            y_selector_angle1="reflectance",
            y_selector_angle2="reflectance",
            save_plots=False,
            sample_id=f"sweep_n1B_{n1_b:.6f}",
        )

        rows.append(
            {
                "n1_B": float(n1_b),
                "reflectance_scale": float(reflectance_scale),
                "theta1_deg": float(theta1_deg),
                "theta2_fit_deg": float(result["theta2_fit_deg"]),
                "d_fit_nominal_nm": float(result["d_fit_nominal_nm"]),
                "d_fit_corrected_nm": float(result["d_fit_corrected_nm"]),
                "delta_d_nm": float(result["delta_d_nm"]),
                "best_objective": float(result["best_objective"]),
                "nominal_objective": float(result["nominal_objective"]),
            }
        )

    fit_df = pd.DataFrame(rows).sort_values("best_objective").reset_index(drop=True)
    fit_df.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return fit_df


def score_n1b_theta_sweep(
    csv_path: Path | None = None,
    theta1_deg: float = 10.0,
    theta2_deg: float = 80.0,
    pol: str = "p",
    reflectance_scale: float = 1.0,
    output_name: str = "n1b_theta_sweep_model_scores.csv",
) -> pd.DataFrame:
    """Score each n1_B sweep group against the physical model without CSV range checks."""
    path = DEG_P_DIR / "p.csv" if csv_path is None else Path(csv_path)
    spec = load_spectrum_csv(path, y_selector=5)
    df = spec.data_table.copy()
    n1_b_values = sorted(np.unique(df.iloc[:, 2].to_numpy(dtype=float)))

    rows: List[Dict[str, float]] = []
    for n1_b in n1_b_values:
        w1_nm, r1 = _extract_curve_from_sweep_table(df, theta1_deg, float(n1_b), reflectance_scale)
        w2_nm, r2 = _extract_curve_from_sweep_table(df, theta2_deg, float(n1_b), reflectance_scale)
        lam_nm, r1_i, r2_i = unify_two_reflectance_curves(
            w1_nm,
            r1,
            w2_nm,
            r2,
            wmin_nm=cfg.LAMBDA_MIN_NM,
            wmax_nm=cfg.LAMBDA_MAX_NM,
            n_lambda=cfg.N_LAMBDA,
        )
        lam = lam_nm * 1e-9

        result = multiscale_dual_search(
            lam=lam,
            R1=r1_i,
            theta1_fixed=theta1_deg,
            R2=r2_i,
            theta2_nominal=theta2_deg,
            n0=cfg.N0,
            n1=cfg.N1,
            n2=cfg.N2,
            pol=pol,
            mix_p_weight=cfg.MIX_P_WEIGHT,
            d_min=cfg.D_MIN,
            d_max=cfg.D_MAX,
            lambda_a=cfg.LAMBDA_A,
            lambda_b=cfg.LAMBDA_B,
            theta2_min=theta2_deg + cfg.THETA2_SEARCH_MIN,
            theta2_max=theta2_deg + cfg.THETA2_SEARCH_MAX,
        )

        rows.append(
            {
                "n1_B": float(n1_b),
                "reflectance_scale": float(reflectance_scale),
                "theta1_deg": float(theta1_deg),
                "theta2_fit_deg": float(result["theta2_fit_deg"]),
                "d_fit_nm": float(result["d_fit_nm"]),
                "best_objective": float(result["best_objective"]),
                "r1_mean": float(np.mean(r1_i)),
                "r2_mean": float(np.mean(r2_i)),
                "r1_min": float(np.min(r1_i)),
                "r1_max": float(np.max(r1_i)),
                "r2_min": float(np.min(r2_i)),
                "r2_max": float(np.max(r2_i)),
            }
        )

    score_df = pd.DataFrame(rows).sort_values("best_objective").reset_index(drop=True)
    score_df.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return score_df


def _extract_curve_from_d_n1b_sweep_table(
    df: pd.DataFrame,
    thickness_m: float,
    theta_deg: float,
    n1_b: float,
    reflectance_scale: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    wavelength_nm = df.iloc[:, 0].to_numpy(dtype=float) * 1e9
    theta_values = _theta_column_to_deg(df.iloc[:, 1].to_numpy(dtype=float))
    thickness_values = df.iloc[:, 2].to_numpy(dtype=float)
    n1_b_values = df.iloc[:, 3].to_numpy(dtype=float)
    reflectance = df.iloc[:, 6].to_numpy(dtype=float) * float(reflectance_scale)

    mask = (
        np.isclose(thickness_values, thickness_m)
        & np.isclose(theta_values, theta_deg)
        & np.isclose(n1_b_values, n1_b)
    )
    if not np.any(mask):
        raise ValueError(
            f"No curve found for d={thickness_m}, theta={theta_deg}, n1_B={n1_b}."
        )

    order = np.argsort(wavelength_nm[mask])
    return wavelength_nm[mask][order], reflectance[mask][order]


def fit_d_n1b_theta_sweep(
    csv_path: Path | None = None,
    theta1_deg: float = 10.0,
    theta2_deg: float = 80.0,
    pol: str = "p",
    reflectance_scale: float = 1.0,
    output_name: str = "d_n1b_theta_sweep_fit_results.csv",
) -> pd.DataFrame:
    """Fit a COMSOL d+n1_B+theta+lambda sweep table."""
    path = DEG_P_DIR / "d_p.csv" if csv_path is None else Path(csv_path)
    spec = load_spectrum_csv(path, y_selector=6)
    df = spec.data_table.copy()

    thickness_values = sorted(np.unique(df.iloc[:, 2].to_numpy(dtype=float)))
    n1_b_values = sorted(np.unique(df.iloc[:, 3].to_numpy(dtype=float)))
    rows: List[Dict[str, float]] = []

    for thickness_m in thickness_values:
        true_thickness_nm = float(thickness_m * 1e9)
        for n1_b in n1_b_values:
            w1_nm, r1 = _extract_curve_from_d_n1b_sweep_table(
                df, float(thickness_m), theta1_deg, float(n1_b), reflectance_scale
            )
            w2_nm, r2 = _extract_curve_from_d_n1b_sweep_table(
                df, float(thickness_m), theta2_deg, float(n1_b), reflectance_scale
            )
            lam_nm, r1_i, r2_i = unify_two_reflectance_curves(
                w1_nm,
                r1,
                w2_nm,
                r2,
                wmin_nm=cfg.LAMBDA_MIN_NM,
                wmax_nm=cfg.LAMBDA_MAX_NM,
                n_lambda=cfg.N_LAMBDA,
            )

            result = multiscale_dual_search(
                lam=lam_nm * 1e-9,
                R1=r1_i,
                theta1_fixed=theta1_deg,
                R2=r2_i,
                theta2_nominal=theta2_deg,
                n0=cfg.N0,
                n1=cfg.N1,
                n2=cfg.N2,
                pol=pol,
                mix_p_weight=cfg.MIX_P_WEIGHT,
                d_min=cfg.D_MIN,
                d_max=cfg.D_MAX,
                lambda_a=cfg.LAMBDA_A,
                lambda_b=cfg.LAMBDA_B,
                theta2_min=theta2_deg + cfg.THETA2_SEARCH_MIN,
                theta2_max=theta2_deg + cfg.THETA2_SEARCH_MAX,
            )

            d_fit_nm = float(result["d_fit_nm"])
            rows.append(
                {
                    "true_thickness_nm": true_thickness_nm,
                    "n1_B": float(n1_b),
                    "theta1_deg": float(theta1_deg),
                    "theta2_fit_deg": float(result["theta2_fit_deg"]),
                    "d_fit_nm": d_fit_nm,
                    "thickness_error_nm": float(d_fit_nm - true_thickness_nm),
                    "abs_thickness_error_nm": float(abs(d_fit_nm - true_thickness_nm)),
                    "best_objective": float(result["best_objective"]),
                    "r1_mean": float(np.mean(r1_i)),
                    "r2_mean": float(np.mean(r2_i)),
                }
            )

    fit_df = pd.DataFrame(rows)
    fit_df = fit_df.sort_values(
        ["true_thickness_nm", "best_objective", "abs_thickness_error_nm"]
    ).reset_index(drop=True)
    fit_df.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return fit_df


def quick_screen_d_n1b_theta_sweep(
    csv_path: Path | None = None,
    theta1_deg: float = 10.0,
    theta2_deg: float = 80.0,
    pol: str = "p",
    d_min_nm: float = 40.0,
    d_max_nm: float = 140.0,
    d_step_nm: float = 1.0,
    theta2_half_range_deg: float = 0.2,
    theta2_step_deg: float = 0.02,
    reflectance_scale: float = 1.0,
    output_name: str = "d_n1b_theta_sweep_quick_screen.csv",
) -> pd.DataFrame:
    """Fast coarse screen for d+n1_B+theta sweep tables."""
    path = DEG_P_DIR / "d_p.csv" if csv_path is None else Path(csv_path)
    spec = load_spectrum_csv(path, y_selector=6)
    df = spec.data_table.copy()

    thickness_values = sorted(np.unique(df.iloc[:, 2].to_numpy(dtype=float)))
    n1_b_values = sorted(np.unique(df.iloc[:, 3].to_numpy(dtype=float)))
    d_grid_nm = np.arange(d_min_nm, d_max_nm + 1e-12, d_step_nm)
    theta2_grid = np.arange(
        theta2_deg - theta2_half_range_deg,
        theta2_deg + theta2_half_range_deg + 1e-12,
        theta2_step_deg,
    )

    rows: List[Dict[str, float]] = []
    for thickness_m in thickness_values:
        true_thickness_nm = float(thickness_m * 1e9)
        for n1_b in n1_b_values:
            w1_nm, r1 = _extract_curve_from_d_n1b_sweep_table(
                df, float(thickness_m), theta1_deg, float(n1_b), reflectance_scale
            )
            w2_nm, r2 = _extract_curve_from_d_n1b_sweep_table(
                df, float(thickness_m), theta2_deg, float(n1_b), reflectance_scale
            )
            lam_nm, r1_i, r2_i = unify_two_reflectance_curves(
                w1_nm,
                r1,
                w2_nm,
                r2,
                wmin_nm=cfg.LAMBDA_MIN_NM,
                wmax_nm=cfg.LAMBDA_MAX_NM,
                n_lambda=cfg.N_LAMBDA,
            )
            lam = lam_nm * 1e-9
            material = _material_params_from_d_n1b_group(df, float(thickness_m), float(n1_b))

            best = None
            for d_nm in d_grid_nm:
                d_m = float(d_nm) * 1e-9
                for theta2_test in theta2_grid:
                    objective = _evaluate_dual_fit_objective_local(
                        lam=lam,
                        r1=r1_i,
                        theta1_deg=theta1_deg,
                        r2=r2_i,
                        theta2_deg=float(theta2_test),
                        d=d_m,
                        pol=pol,
                        n0=cfg.N0,
                        n1_a=material["n1_A"],
                        n1_b=material["n1_B"],
                        n1_c=material["n1_C"],
                        n2_a=material["n2_A"],
                        n2_b=material["n2_B"],
                        n2_c=material["n2_C"],
                    )
                    if best is None or objective < best["objective"]:
                        best = {
                            "d_fit_nm": float(d_nm),
                            "theta2_fit_deg": float(theta2_test),
                            "objective": float(objective),
                        }

            rows.append(
                {
                    "true_thickness_nm": true_thickness_nm,
                    "n1_B": float(n1_b),
                    "n1_A": float(material["n1_A"]),
                    "n1_C": float(material["n1_C"]),
                    "n2_A": float(material["n2_A"]),
                    "n2_B": float(material["n2_B"]),
                    "n2_C": float(material["n2_C"]),
                    "theta1_deg": float(theta1_deg),
                    "theta2_fit_deg": float(best["theta2_fit_deg"]),
                    "d_fit_nm": float(best["d_fit_nm"]),
                    "thickness_error_nm": float(best["d_fit_nm"] - true_thickness_nm),
                    "abs_thickness_error_nm": float(abs(best["d_fit_nm"] - true_thickness_nm)),
                    "best_objective": float(best["objective"]),
                    "screen_d_step_nm": float(d_step_nm),
                    "screen_theta2_step_deg": float(theta2_step_deg),
                }
            )

    screen_df = pd.DataFrame(rows)
    screen_df = screen_df.sort_values(
        ["true_thickness_nm", "best_objective", "abs_thickness_error_nm"]
    ).reset_index(drop=True)
    screen_df.to_csv(output_file(output_name), index=False, encoding="utf-8-sig")
    return screen_df
