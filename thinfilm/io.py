"""CSV and COMSOL table I/O helpers.

This module groups data-loading functions that currently live in thinfilm_core.py.
The implementation is re-exported from the legacy engine to keep behavior stable.
"""

from __future__ import annotations

from thinfilm_core import (
    SpectrumData,
    export_clean_csv,
    extract_constant_theta_deg,
    load_reflectance_spec,
    load_spectrum_csv,
    preview_csv,
    read_reflectance_csv,
    validate_dual_fit_inputs,
    validate_single_fit_input_theta,
)

__all__ = [
    "SpectrumData",
    "export_clean_csv",
    "extract_constant_theta_deg",
    "load_reflectance_spec",
    "load_spectrum_csv",
    "preview_csv",
    "read_reflectance_csv",
    "validate_dual_fit_inputs",
    "validate_single_fit_input_theta",
]
