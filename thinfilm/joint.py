from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

from . import config as cfg
from .io import load_spectrum_csv
from .objectives import evaluate_curve_objective, smooth_signal_1d, standardize_signal
from .optics import unify_two_reflectance_curves
from .paths import DEG_P_DIR, output_file


@dataclass
class JointSampleData:
    sample_id: str
    source_desc: str
    lam_m: np.ndarray
    r1: np.ndarray
    r2: np.ndarray
    theta1_deg: float
    theta2_nominal_deg: float
    nominal_thickness_nm: float | None


def _theta_column_to_deg(theta_values: np.ndarray) -> np.ndarray:
    theta_values = np.asarray(theta_values, dtype=float)
    finite = theta_values[np.isfinite(theta_values)]
    if len(finite) > 0 and np.nanmax(np.abs(finite)) <= 2.5 * np.pi:
        return np.rad2deg(theta_values)
    return theta_values


def _cauchy_index_profile(
    lam_m: np.ndarray,
    n_a: float,
    n_b: float,
    n_c: float,
) -> np.ndarray:
    lam_um = np.clip(np.asarray(lam_m, dtype=float) * 1e6, 1e-9, None)
    return float(n_a) + float(n_b) / (lam_um ** 2) + float(n_c) / (lam_um ** 4)


def _thinfilm_reflectance_angle_local(
    lam_m: np.ndarray,
    d_m: float,
    theta0_deg: float,
    pol: str,
    n0: float,
    n1_a: float,
    n1_b: float,
    n1_c: float,
    n2_a: float,
    n2_b: float,
    n2_c: float,
    mix_p_weight: float,
) -> np.ndarray:
    theta0 = np.deg2rad(theta0_deg)
    n0_arr = np.full_like(lam_m, float(n0), dtype=float)
    n1_arr = _cauchy_index_profile(lam_m, n1_a, n1_b, n1_c)
    n2_arr = _cauchy_index_profile(lam_m, n2_a, n2_b, n2_c)

    sin_theta1 = np.clip(n0_arr * np.sin(theta0) / n1_arr, -1.0, 1.0)
    sin_theta2 = np.clip(n0_arr * np.sin(theta0) / n2_arr, -1.0, 1.0)
    theta1 = np.arcsin(sin_theta1)
    theta2 = np.arcsin(sin_theta2)

    c0 = np.cos(theta0)
    c1 = np.cos(theta1)
    c2 = np.cos(theta2)
    beta = 2.0 * np.pi * n1_arr * float(d_m) * c1 / lam_m
    phase = np.exp(2j * beta)

    r01_s = (n0_arr * c0 - n1_arr * c1) / (n0_arr * c0 + n1_arr * c1)
    r12_s = (n1_arr * c1 - n2_arr * c2) / (n1_arr * c1 + n2_arr * c2)
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
    lam_m: np.ndarray,
    r1: np.ndarray,
    theta1_deg: float,
    r2: np.ndarray,
    theta2_deg: float,
    d_m: float,
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
        lam_m,
        d_m,
        theta1_deg,
        pol,
        n0,
        n1_a,
        n1_b,
        n1_c,
        n2_a,
        n2_b,
        n2_c,
        cfg.MIX_P_WEIGHT,
    )
    rm2 = _thinfilm_reflectance_angle_local(
        lam_m,
        d_m,
        theta2_deg,
        pol,
        n0,
        n1_a,
        n1_b,
        n1_c,
        n2_a,
        n2_b,
        n2_c,
        cfg.MIX_P_WEIGHT,
    )

    err1, (a1, b1), _ = evaluate_curve_objective(
        lam=lam_m,
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
        lam=lam_m,
        y_obs=r2,
        y_model=rm2,
        lambda_a=cfg.LAMBDA_A,
        lambda_b=cfg.LAMBDA_B,
        smooth_window=cfg.OBJECTIVE_SMOOTH_WINDOW,
        weight_level=cfg.OBJECTIVE_WEIGHT_LEVEL,
        weight_shape=cfg.OBJECTIVE_WEIGHT_SHAPE,
        weight_slope=cfg.OBJECTIVE_WEIGHT_SLOPE,
    )

    lam_span = max(float(np.max(lam_m) - np.min(lam_m)), 1e-18)
    lam_norm = (lam_m - np.mean(lam_m)) / lam_span
    rm1_adj = rm1 + a1 + b1 * lam_norm
    rm2_adj = rm2 + a2 + b2 * lam_norm

    delta_obs = smooth_signal_1d(r2 - r1, window=cfg.OBJECTIVE_SMOOTH_WINDOW)
    delta_model = smooth_signal_1d(rm2_adj - rm1_adj, window=cfg.OBJECTIVE_SMOOTH_WINDOW)
    delta_shape_err = float(
        np.mean((standardize_signal(delta_obs) - standardize_signal(delta_model)) ** 2)
    )
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


def _parse_nominal_thickness_nm(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*nm", str(text), flags=re.IGNORECASE)
    if match is None:
        return None
    return float(match.group(1))


def _find_theta_column(df: pd.DataFrame, theta_targets_deg: Sequence[float]) -> int:
    best_idx = None
    best_score = None
    rounded_targets = [round(float(x), 6) for x in theta_targets_deg]
    for col_idx in range(df.shape[1]):
        values = df.iloc[:, col_idx].to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        if len(finite) < 2:
            continue
        theta_deg = _theta_column_to_deg(finite)
        uniq = sorted(set(np.round(theta_deg, 6)))
        if len(uniq) < len(rounded_targets) or len(uniq) > 20:
            continue
        max_dist = max(min(abs(u - target) for u in uniq) for target in rounded_targets)
        if max_dist > 1e-3:
            continue
        score = (max_dist, len(uniq), col_idx)
        if best_score is None or score < best_score:
            best_score = score
            best_idx = col_idx

    if best_idx is None:
        raise ValueError(
            f"Could not find a theta column matching targets {list(theta_targets_deg)}."
        )
    return int(best_idx)


def _load_sample_from_combined_csv(
    sample_id: str,
    csv_path: Path,
    theta1_deg: float,
    theta2_deg: float,
    y_selector: int | str | None,
    nominal_thickness_nm: float | None,
) -> JointSampleData:
    spec = load_spectrum_csv(csv_path, y_selector=y_selector)
    df = spec.data_table.copy()
    if isinstance(y_selector, int):
        y_idx = int(y_selector)
    else:
        y_idx = int(spec.all_column_labels.index(spec.y_label))
    theta_idx = _find_theta_column(df, [theta1_deg, theta2_deg])

    wavelength_nm = df.iloc[:, 0].to_numpy(dtype=float) * 1e9
    theta_deg = _theta_column_to_deg(df.iloc[:, theta_idx].to_numpy(dtype=float))
    reflectance = df.iloc[:, y_idx].to_numpy(dtype=float)

    curves: Dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for theta_target in (theta1_deg, theta2_deg):
        mask = np.isclose(theta_deg, theta_target)
        if not np.any(mask):
            raise ValueError(
                f"Sample {sample_id} has no rows for theta={theta_target:.6f} deg."
            )
        order = np.argsort(wavelength_nm[mask])
        curves[float(theta_target)] = (
            wavelength_nm[mask][order],
            reflectance[mask][order],
        )

    lam_nm, r1, r2 = unify_two_reflectance_curves(
        curves[float(theta1_deg)][0],
        curves[float(theta1_deg)][1],
        curves[float(theta2_deg)][0],
        curves[float(theta2_deg)][1],
        wmin_nm=cfg.LAMBDA_MIN_NM,
        wmax_nm=cfg.LAMBDA_MAX_NM,
        n_lambda=cfg.N_LAMBDA,
    )
    return JointSampleData(
        sample_id=sample_id,
        source_desc=str(Path(csv_path).name),
        lam_m=lam_nm * 1e-9,
        r1=r1,
        r2=r2,
        theta1_deg=float(theta1_deg),
        theta2_nominal_deg=float(theta2_deg),
        nominal_thickness_nm=nominal_thickness_nm,
    )


def _load_sample_from_two_files(
    sample_id: str,
    csv_angle1: Path,
    csv_angle2: Path,
    theta1_deg: float,
    theta2_deg: float,
    y_selector_angle1: int | str | None,
    y_selector_angle2: int | str | None,
    nominal_thickness_nm: float | None,
) -> JointSampleData:
    spec1 = load_spectrum_csv(csv_angle1, y_selector=y_selector_angle1)
    spec2 = load_spectrum_csv(csv_angle2, y_selector=y_selector_angle2)
    lam_nm, r1, r2 = unify_two_reflectance_curves(
        spec1.x_nm,
        spec1.y,
        spec2.x_nm,
        spec2.y,
        wmin_nm=cfg.LAMBDA_MIN_NM,
        wmax_nm=cfg.LAMBDA_MAX_NM,
        n_lambda=cfg.N_LAMBDA,
    )
    return JointSampleData(
        sample_id=sample_id,
        source_desc=f"{Path(csv_angle1).name}+{Path(csv_angle2).name}",
        lam_m=lam_nm * 1e-9,
        r1=r1,
        r2=r2,
        theta1_deg=float(theta1_deg),
        theta2_nominal_deg=float(theta2_deg),
        nominal_thickness_nm=nominal_thickness_nm,
    )


def _load_joint_sample(
    sample_spec: Dict[str, Any],
    theta1_deg: float,
    theta2_deg: float,
) -> JointSampleData:
    sample_id = str(
        sample_spec.get("sample_id")
        or sample_spec.get("combined_csv")
        or sample_spec.get("csv_angle1")
        or "sample"
    )
    nominal_thickness_nm = sample_spec.get("nominal_thickness_nm")
    if nominal_thickness_nm is None:
        nominal_thickness_nm = _parse_nominal_thickness_nm(sample_id)
    if nominal_thickness_nm is None and "combined_csv" in sample_spec:
        nominal_thickness_nm = _parse_nominal_thickness_nm(Path(sample_spec["combined_csv"]).name)
    if nominal_thickness_nm is None and "csv_angle1" in sample_spec:
        nominal_thickness_nm = _parse_nominal_thickness_nm(Path(sample_spec["csv_angle1"]).name)

    if "combined_csv" in sample_spec:
        return _load_sample_from_combined_csv(
            sample_id=sample_id,
            csv_path=Path(sample_spec["combined_csv"]),
            theta1_deg=theta1_deg,
            theta2_deg=theta2_deg,
            y_selector=sample_spec.get("y_selector", 3),
            nominal_thickness_nm=nominal_thickness_nm,
        )

    return _load_sample_from_two_files(
        sample_id=sample_id,
        csv_angle1=Path(sample_spec["csv_angle1"]),
        csv_angle2=Path(sample_spec["csv_angle2"]),
        theta1_deg=theta1_deg,
        theta2_deg=theta2_deg,
        y_selector_angle1=sample_spec.get("y_selector_angle1"),
        y_selector_angle2=sample_spec.get("y_selector_angle2"),
        nominal_thickness_nm=nominal_thickness_nm,
    )


def _sample_thickness_grid_nm(
    sample: JointSampleData,
    half_range_nm: float,
    step_nm: float,
) -> np.ndarray:
    if sample.nominal_thickness_nm is None:
        center_nm = 0.5 * (cfg.D_MIN + cfg.D_MAX) * 1e9
    else:
        center_nm = float(sample.nominal_thickness_nm)
    start_nm = max(5.0, center_nm - float(half_range_nm))
    stop_nm = center_nm + float(half_range_nm)
    return np.arange(start_nm, stop_nm + 1e-12, float(step_nm))


def _search_single_sample_best_fit(
    sample: JointSampleData,
    pol: str,
    n1_a: float,
    n1_b: float,
    d_grid_nm: np.ndarray,
    theta2_grid_deg: np.ndarray,
) -> Dict[str, float]:
    best = None
    for d_nm in d_grid_nm:
        d_m = float(d_nm) * 1e-9
        for theta2_deg in theta2_grid_deg:
            objective = _evaluate_dual_fit_objective_local(
                lam_m=sample.lam_m,
                r1=sample.r1,
                theta1_deg=sample.theta1_deg,
                r2=sample.r2,
                theta2_deg=float(theta2_deg),
                d_m=d_m,
                pol=pol,
                n0=cfg.N0,
                n1_a=float(n1_a),
                n1_b=float(n1_b),
                n1_c=0.0,
                n2_a=cfg.N2,
                n2_b=0.0,
                n2_c=0.0,
            )
            if best is None or objective < best["best_objective"]:
                thickness_error_nm = None
                abs_thickness_error_nm = None
                if sample.nominal_thickness_nm is not None:
                    thickness_error_nm = float(d_nm - sample.nominal_thickness_nm)
                    abs_thickness_error_nm = float(abs(thickness_error_nm))
                best = {
                    "d_fit_nm": float(d_nm),
                    "theta2_fit_deg": float(theta2_deg),
                    "best_objective": float(objective),
                    "thickness_error_nm": thickness_error_nm,
                    "abs_thickness_error_nm": abs_thickness_error_nm,
                }

    if best is None:
        raise RuntimeError(f"No valid fit candidate found for sample {sample.sample_id}.")
    return best


def _summarize_joint_candidate(
    sample_results: List[Dict[str, Any]],
    n1_a: float,
    n1_b: float,
    stage: str,
) -> Dict[str, Any]:
    objectives = [float(item["best_objective"]) for item in sample_results]
    abs_errors = [
        float(item["abs_thickness_error_nm"])
        for item in sample_results
        if item["abs_thickness_error_nm"] is not None
    ]
    summary: Dict[str, Any] = {
        "stage": stage,
        "n1_A": float(n1_a),
        "n1_B": float(n1_b),
        "joint_objective": float(np.mean(objectives)),
        "max_sample_objective": float(np.max(objectives)),
        "n_samples": int(len(sample_results)),
    }
    if len(abs_errors) == len(sample_results):
        summary["mean_abs_thickness_error_nm"] = float(np.mean(abs_errors))
        summary["max_abs_thickness_error_nm"] = float(np.max(abs_errors))
    else:
        summary["mean_abs_thickness_error_nm"] = None
        summary["max_abs_thickness_error_nm"] = None
    return summary


def fit_joint_shared_material_two_angle_samples(
    sample_specs: Sequence[Dict[str, Any]],
    theta1_deg: float = 10.0,
    theta2_deg: float = 80.0,
    pol: str = "p",
    n1_a_min: float = 1.36,
    n1_a_max: float = 1.40,
    n1_a_step: float = 0.002,
    n1_b_min: float = 0.0,
    n1_b_max: float = 0.012,
    n1_b_step: float = 0.001,
    coarse_thickness_half_range_nm: float = 20.0,
    coarse_d_step_nm: float = 1.0,
    refine_half_window_nm: float = 4.0,
    refine_d_step_nm: float = 0.25,
    refine_theta2_half_range_deg: float = 0.10,
    refine_theta2_step_deg: float = 0.01,
    top_k_shared_candidates: int = 5,
    output_prefix: str = "joint_shared_material_fit",
) -> Dict[str, Any]:
    if len(sample_specs) == 0:
        raise ValueError("sample_specs must contain at least one sample.")

    samples = [
        _load_joint_sample(sample_spec, theta1_deg=float(theta1_deg), theta2_deg=float(theta2_deg))
        for sample_spec in sample_specs
    ]

    n1_a_grid = np.arange(float(n1_a_min), float(n1_a_max) + 1e-12, float(n1_a_step))
    n1_b_grid = np.arange(float(n1_b_min), float(n1_b_max) + 1e-12, float(n1_b_step))
    coarse_rows: List[Dict[str, Any]] = []
    coarse_sample_rows: List[Dict[str, Any]] = []

    for n1_a in n1_a_grid:
        for n1_b in n1_b_grid:
            sample_results: List[Dict[str, Any]] = []
            for sample in samples:
                best = _search_single_sample_best_fit(
                    sample=sample,
                    pol=pol,
                    n1_a=float(n1_a),
                    n1_b=float(n1_b),
                    d_grid_nm=_sample_thickness_grid_nm(
                        sample,
                        half_range_nm=coarse_thickness_half_range_nm,
                        step_nm=coarse_d_step_nm,
                    ),
                    theta2_grid_deg=np.array([float(theta2_deg)], dtype=float),
                )
                sample_results.append(
                    {
                        "sample_id": sample.sample_id,
                        "nominal_thickness_nm": sample.nominal_thickness_nm,
                        "n1_A": float(n1_a),
                        "n1_B": float(n1_b),
                        **best,
                    }
                )
                coarse_sample_rows.append(
                    {
                        "sample_id": sample.sample_id,
                        "source_desc": sample.source_desc,
                        "nominal_thickness_nm": sample.nominal_thickness_nm,
                        "n1_A": float(n1_a),
                        "n1_B": float(n1_b),
                        **best,
                    }
                )

            joint_row = _summarize_joint_candidate(
                sample_results=sample_results,
                n1_a=float(n1_a),
                n1_b=float(n1_b),
                stage="coarse",
            )
            coarse_rows.append(joint_row)

    coarse_df = pd.DataFrame(coarse_rows).sort_values(
        ["joint_objective", "mean_abs_thickness_error_nm", "max_sample_objective"],
        na_position="last",
    ).reset_index(drop=True)
    coarse_sample_df = pd.DataFrame(coarse_sample_rows).sort_values(
        ["n1_A", "n1_B", "sample_id"]
    ).reset_index(drop=True)
    coarse_csv = output_file(f"{output_prefix}_coarse_grid.csv")
    coarse_df.to_csv(coarse_csv, index=False, encoding="utf-8-sig")
    coarse_sample_csv = output_file(f"{output_prefix}_coarse_samples.csv")
    coarse_sample_df.to_csv(coarse_sample_csv, index=False, encoding="utf-8-sig")

    top_candidates = coarse_df.head(int(top_k_shared_candidates))
    refine_joint_rows: List[Dict[str, Any]] = []
    refine_sample_rows: List[Dict[str, Any]] = []

    for _, cand in top_candidates.iterrows():
        n1_a = float(cand["n1_A"])
        n1_b = float(cand["n1_B"])
        sample_results = []
        for sample in samples:
            center_nm = float(sample.nominal_thickness_nm or 0.5 * (cfg.D_MIN + cfg.D_MAX) * 1e9)
            coarse_match = coarse_sample_df[
                np.isclose(coarse_sample_df["n1_A"], n1_a)
                & np.isclose(coarse_sample_df["n1_B"], n1_b)
                & (coarse_sample_df["sample_id"] == sample.sample_id)
            ]
            if len(coarse_match) > 0:
                center_nm = float(coarse_match.iloc[0]["d_fit_nm"])
            best = _search_single_sample_best_fit(
                sample=sample,
                pol=pol,
                n1_a=n1_a,
                n1_b=n1_b,
                d_grid_nm=np.arange(
                    max(5.0, center_nm - refine_half_window_nm),
                    center_nm + refine_half_window_nm + 1e-12,
                    refine_d_step_nm,
                ),
                theta2_grid_deg=np.arange(
                    float(theta2_deg) - float(refine_theta2_half_range_deg),
                    float(theta2_deg) + float(refine_theta2_half_range_deg) + 1e-12,
                    float(refine_theta2_step_deg),
                ),
            )
            result_row = {
                "sample_id": sample.sample_id,
                "source_desc": sample.source_desc,
                "nominal_thickness_nm": sample.nominal_thickness_nm,
                "n1_A": n1_a,
                "n1_B": n1_b,
                **best,
            }
            sample_results.append(result_row)
            refine_sample_rows.append(result_row)

        refine_joint_rows.append(
            _summarize_joint_candidate(
                sample_results=sample_results,
                n1_a=n1_a,
                n1_b=n1_b,
                stage="refine",
            )
        )

    refine_joint_df = pd.DataFrame(refine_joint_rows).sort_values(
        ["joint_objective", "mean_abs_thickness_error_nm", "max_sample_objective"],
        na_position="last",
    ).reset_index(drop=True)
    refine_joint_csv = output_file(f"{output_prefix}_refine_joint.csv")
    refine_joint_df.to_csv(refine_joint_csv, index=False, encoding="utf-8-sig")

    refine_sample_df = pd.DataFrame(refine_sample_rows).sort_values(
        ["n1_A", "n1_B", "sample_id"]
    ).reset_index(drop=True)
    refine_sample_csv = output_file(f"{output_prefix}_refine_samples.csv")
    refine_sample_df.to_csv(refine_sample_csv, index=False, encoding="utf-8-sig")

    best_joint = refine_joint_df.iloc[0]
    best_mask = np.isclose(refine_sample_df["n1_A"], float(best_joint["n1_A"])) & np.isclose(
        refine_sample_df["n1_B"], float(best_joint["n1_B"])
    )
    best_samples_df = refine_sample_df.loc[best_mask].copy().reset_index(drop=True)

    result: Dict[str, Any] = {
        "theta1_deg": float(theta1_deg),
        "theta2_nominal_deg": float(theta2_deg),
        "pol": str(pol),
        "best_shared_n1_A": float(best_joint["n1_A"]),
        "best_shared_n1_B": float(best_joint["n1_B"]),
        "joint_best_objective": float(best_joint["joint_objective"]),
        "mean_abs_thickness_error_nm": (
            None
            if pd.isna(best_joint["mean_abs_thickness_error_nm"])
            else float(best_joint["mean_abs_thickness_error_nm"])
        ),
        "max_abs_thickness_error_nm": (
            None
            if pd.isna(best_joint["max_abs_thickness_error_nm"])
            else float(best_joint["max_abs_thickness_error_nm"])
        ),
        "samples": best_samples_df.to_dict(orient="records"),
        "coarse_grid_csv": str(coarse_csv),
        "coarse_samples_csv": str(coarse_sample_csv),
        "refine_joint_csv": str(refine_joint_csv),
        "refine_samples_csv": str(refine_sample_csv),
    }

    summary_json = output_file(f"{output_prefix}_summary.json")
    summary_txt = output_file(f"{output_prefix}_summary.txt")
    summary_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "Joint shared-material fit",
        "=" * 88,
        f"theta1_deg               = {result['theta1_deg']:.6f}",
        f"theta2_nominal_deg       = {result['theta2_nominal_deg']:.6f}",
        f"pol                      = {result['pol']}",
        f"best_shared_n1_A         = {result['best_shared_n1_A']:.6f}",
        f"best_shared_n1_B         = {result['best_shared_n1_B']:.6f}",
        f"joint_best_objective     = {result['joint_best_objective']:.12e}",
    ]
    if result["mean_abs_thickness_error_nm"] is not None:
        lines.append(f"mean_abs_thickness_err   = {result['mean_abs_thickness_error_nm']:.6f} nm")
        lines.append(f"max_abs_thickness_err    = {result['max_abs_thickness_error_nm']:.6f} nm")
    lines.append("-" * 88)
    for item in result["samples"]:
        lines.append(
            f"{item['sample_id']}: d_fit = {float(item['d_fit_nm']):.6f} nm | "
            f"theta2_fit = {float(item['theta2_fit_deg']):.6f} deg | "
            f"objective = {float(item['best_objective']):.12e}"
        )
    summary_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return result


def fit_joint_p_80_100_case(output_prefix: str = "joint_p_80_100_case") -> Dict[str, Any]:
    return fit_joint_shared_material_two_angle_samples(
        sample_specs=[
            {
                "sample_id": "80nm_p",
                "combined_csv": DEG_P_DIR / "80nm_p.csv",
                "y_selector": 4,
                "nominal_thickness_nm": 80.0,
            },
            {
                "sample_id": "100nm_p",
                "combined_csv": DEG_P_DIR / "100nm_p.csv",
                "y_selector": 4,
                "nominal_thickness_nm": 100.0,
            },
        ],
        theta1_deg=10.0,
        theta2_deg=80.0,
        pol="p",
        n1_a_min=1.36,
        n1_a_max=1.40,
        n1_a_step=0.002,
        n1_b_min=0.0,
        n1_b_max=0.012,
        n1_b_step=0.001,
        coarse_thickness_half_range_nm=20.0,
        coarse_d_step_nm=1.0,
        refine_half_window_nm=4.0,
        refine_d_step_nm=0.25,
        refine_theta2_half_range_deg=0.10,
        refine_theta2_step_deg=0.01,
        top_k_shared_candidates=5,
        output_prefix=output_prefix,
    )
