from __future__ import annotations

from typing import Any, Dict, Sequence

import numpy as np

from .models import GuidedGratingSpec, GratingSweepConfig


def _default_wavelength_grid_nm(
    spec: GuidedGratingSpec,
    sweep: GratingSweepConfig | None = None,
) -> np.ndarray:
    if sweep is None:
        return np.arange(spec.lambda0_nm - 100.0, spec.lambda0_nm + 100.0 + 1e-12, 0.5)
    return np.arange(
        float(sweep.wavelength_start_nm),
        float(sweep.wavelength_stop_nm) + 1e-12,
        float(sweep.wavelength_step_nm),
    )


def validate_guided_grating_spec(spec: GuidedGratingSpec) -> None:
    if spec.period_nm <= 0.0:
        raise ValueError("period_nm must be positive.")
    if spec.waveguide_thickness_nm <= 0.0:
        raise ValueError("waveguide_thickness_nm must be positive.")
    if spec.grating_thickness_nm <= 0.0:
        raise ValueError("grating_thickness_nm must be positive.")
    if not (0.0 < spec.fill_factor < 1.0):
        raise ValueError("fill_factor must be between 0 and 1.")
    if spec.n_waveguide <= 0.0 or spec.n_grating <= 0.0 or spec.n_substrate <= 0.0:
        raise ValueError("All refractive indices must be positive.")
    if str(spec.pol).upper() not in {"TE", "TM"}:
        raise ValueError("pol must be 'TE' or 'TM'.")


def simulate_guided_grating_placeholder(
    spec: GuidedGratingSpec,
    wavelengths_nm: Sequence[float] | None = None,
    sweep: GratingSweepConfig | None = None,
) -> Dict[str, Any]:
    """Return a clearly-labeled placeholder resonance spectrum.

    This is not RCWA and not COMSOL. It is a smooth, physically-inspired
    surrogate that lets us build the branch structure, exports, and UI first.
    Replace this function with a real backend later.
    """

    validate_guided_grating_spec(spec)
    wl = np.asarray(
        wavelengths_nm if wavelengths_nm is not None else _default_wavelength_grid_nm(spec, sweep),
        dtype=float,
    )

    # A simple surrogate guided-mode resonance shape with geometry-sensitive
    # center shift and linewidth. This is only for branch scaffolding.
    fill_shift_nm = 80.0 * (float(spec.fill_factor) - 0.5)
    thickness_shift_nm = 0.35 * (float(spec.waveguide_thickness_nm) - 180.0)
    period_shift_nm = 0.12 * (float(spec.period_nm) - 780.0)
    theta_shift_nm = -0.9 * float(spec.theta_deg)
    pol_shift_nm = 6.0 if str(spec.pol).upper() == "TM" else 0.0
    center_nm = (
        float(spec.lambda0_nm)
        + fill_shift_nm
        + thickness_shift_nm
        + period_shift_nm
        + theta_shift_nm
        + pol_shift_nm
    )

    base_width_nm = 5.0 + 18.0 * abs(float(spec.fill_factor) - 0.5)
    width_nm = max(1.5, base_width_nm + 0.03 * abs(float(spec.waveguide_thickness_nm) - 180.0))

    contrast = min(0.995, 0.75 + 0.08 * (float(spec.n_waveguide) - float(spec.n_substrate)))
    baseline = max(0.02, 0.06 - 0.01 * (float(spec.n_waveguide) - float(spec.n_incident)))

    lorentz = 1.0 / (1.0 + ((wl - center_nm) / width_nm) ** 2)
    side_ripple = 0.015 * np.cos(2.0 * np.pi * (wl - float(spec.lambda0_nm)) / 55.0)
    r_vals = np.clip(baseline + contrast * lorentz + side_ripple, 0.0, 1.0)

    # A simple loss model hook, still placeholder but useful for later pipeline work.
    loss_level = min(0.12, 0.02 + 0.5 * max(float(spec.k_waveguide), 0.0) + 0.3 * max(float(spec.k_grating), 0.0))
    a_vals = np.clip(loss_level * lorentz, 0.0, 0.2)
    t_vals = np.clip(1.0 - r_vals - a_vals, 0.0, 1.0)

    return {
        "sample_id": spec.sample_id,
        "model_type": "guided_grating_placeholder_surrogate",
        "is_placeholder": True,
        "backend": "placeholder",
        "warning": "This branch currently uses a placeholder resonance surrogate, not RCWA/COMSOL.",
        "spec": spec.to_dict(),
        "wavelength_nm": wl,
        "R": r_vals,
        "T": t_vals,
        "A": a_vals,
        "resonance_center_estimate_nm": float(center_nm),
        "resonance_width_estimate_nm": float(width_nm),
    }
