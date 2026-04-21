"""Thickness inversion and objective-function helpers."""

from __future__ import annotations

from thinfilm_core import (
    evaluate_curve_objective,
    evaluate_dual_fit_objective,
    fit_dual_csv_from_files,
    fit_dual_csv_with_theta2_search_from_files,
    fit_linear_baseline,
    fit_mix_weight_from_dual_csv,
    invert_thickness_dual_detrend,
    invert_thickness_dual_only,
    invert_thickness_dual_with_theta2_search,
    invert_thickness_single_detrend,
    invert_thickness_single_only,
    multiscale_dual_search,
    pick_distinct_search_seeds,
    run_dual_theta2_search_once,
)

__all__ = [
    "evaluate_curve_objective",
    "evaluate_dual_fit_objective",
    "fit_dual_csv_from_files",
    "fit_dual_csv_with_theta2_search_from_files",
    "fit_linear_baseline",
    "fit_mix_weight_from_dual_csv",
    "invert_thickness_dual_detrend",
    "invert_thickness_dual_only",
    "invert_thickness_dual_with_theta2_search",
    "invert_thickness_single_detrend",
    "invert_thickness_single_only",
    "multiscale_dual_search",
    "pick_distinct_search_seeds",
    "run_dual_theta2_search_once",
]
