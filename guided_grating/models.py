from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class GuidedGratingSpec:
    """Minimal parameter set for the guided grating branch.

    The current branch scaffold focuses on a 1D periodic guided grating reflector.
    This is only the geometry/material container; the actual solver backend may
    later be replaced by COMSOL-driven data, RCWA, or another physical solver.
    """

    sample_id: str
    period_nm: float
    waveguide_thickness_nm: float
    grating_thickness_nm: float
    fill_factor: float
    n_incident: float
    n_waveguide: float
    n_grating: float
    n_substrate: float
    theta_deg: float = 0.0
    pol: str = "TE"
    lambda0_nm: float = 1550.0
    k_waveguide: float = 0.0
    k_grating: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GratingSweepConfig:
    """Simple sweep configuration for future parameter scans."""

    wavelength_start_nm: float = 1450.0
    wavelength_stop_nm: float = 1650.0
    wavelength_step_nm: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
