from __future__ import annotations

from typing import Any, Dict

from .export import export_guided_grating_result
from .models import GuidedGratingSpec, GratingSweepConfig
from .solver import simulate_guided_grating_placeholder
from .spectra import summarize_guided_grating_spectrum


def build_minimal_demo_spec() -> GuidedGratingSpec:
    """Minimal starter case for the guided grating branch."""

    return GuidedGratingSpec(
        sample_id="minimal_branch_case",
        period_nm=780.0,
        waveguide_thickness_nm=180.0,
        grating_thickness_nm=85.0,
        fill_factor=0.52,
        n_incident=1.0,
        n_waveguide=2.0,
        n_grating=2.0,
        n_substrate=1.45,
        theta_deg=0.0,
        pol="TE",
        lambda0_nm=1550.0,
        notes="Branch scaffold only. Replace placeholder solver with COMSOL/RCWA later.",
    )


def run_minimal_demo(prefix: str = "guided_grating_demo") -> Dict[str, Any]:
    spec = build_minimal_demo_spec()
    sweep = GratingSweepConfig(
        wavelength_start_nm=1450.0,
        wavelength_stop_nm=1650.0,
        wavelength_step_nm=0.5,
    )
    result = simulate_guided_grating_placeholder(spec=spec, sweep=sweep)
    summary = summarize_guided_grating_spectrum(result)
    files = export_guided_grating_result(result, prefix=prefix)
    return {
        "spec": spec.to_dict(),
        "summary": summary,
        "files": files,
        "warning": result.get("warning"),
    }
