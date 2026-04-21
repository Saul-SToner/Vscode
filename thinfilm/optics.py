"""Thin-film optical forward model helpers."""

from __future__ import annotations

from thinfilm_core import (
    build_endpoint_blend_curve,
    evaluate_dispersion_profile,
    interpolate_to_grid,
    resolve_dual_fit_curves,
    thinfilm_reflectance_angle,
    unify_two_reflectance_curves,
)

__all__ = [
    "build_endpoint_blend_curve",
    "evaluate_dispersion_profile",
    "interpolate_to_grid",
    "resolve_dual_fit_curves",
    "thinfilm_reflectance_angle",
    "unify_two_reflectance_curves",
]
