from __future__ import annotations

from typing import Any, Dict

import numpy as np


def summarize_guided_grating_spectrum(result: Dict[str, Any]) -> Dict[str, Any]:
    wl = np.asarray(result["wavelength_nm"], dtype=float)
    r_vals = np.asarray(result["R"], dtype=float)
    t_vals = np.asarray(result["T"], dtype=float)
    a_vals = np.asarray(result["A"], dtype=float)

    peak_idx = int(np.argmax(r_vals))
    peak_r = float(r_vals[peak_idx])
    peak_wl = float(wl[peak_idx])
    half_level = 0.5 * peak_r
    above = np.where(r_vals >= half_level)[0]
    fwhm_nm = float(wl[above[-1]] - wl[above[0]]) if len(above) >= 2 else 0.0

    return {
        "peak_reflectance": peak_r,
        "peak_wavelength_nm": peak_wl,
        "fwhm_nm": fwhm_nm,
        "min_reflectance": float(np.min(r_vals)),
        "min_reflectance_wavelength_nm": float(wl[int(np.argmin(r_vals))]),
        "max_transmittance": float(np.max(t_vals)),
        "max_absorptance": float(np.max(a_vals)),
        "wavelength_start_nm": float(wl[0]),
        "wavelength_stop_nm": float(wl[-1]),
        "num_points": int(wl.size),
        "backend": result.get("backend"),
        "is_placeholder": bool(result.get("is_placeholder", False)),
    }
