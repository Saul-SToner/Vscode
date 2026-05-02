"""Guided grating branch.

This package is intentionally kept separate from ``thinfilm/`` so the
existing teaching main branch and inversion pipeline stay stable.
"""

from .examples import build_minimal_demo_spec, run_minimal_demo
from .export import export_guided_grating_result
from .models import GuidedGratingSpec, GratingSweepConfig
from .solver import simulate_guided_grating_placeholder
from .spectra import summarize_guided_grating_spectrum

__all__ = [
    "GuidedGratingSpec",
    "GratingSweepConfig",
    "build_minimal_demo_spec",
    "run_minimal_demo",
    "simulate_guided_grating_placeholder",
    "summarize_guided_grating_spectrum",
    "export_guided_grating_result",
]
