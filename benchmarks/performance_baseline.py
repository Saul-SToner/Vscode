"""Performance baseline for TMM core computation.

This script measures the execution time of key TMM operations
to establish a baseline before vectorization.

Usage:
    python benchmarks/performance_baseline.py
"""

from __future__ import annotations

import time
from typing import Dict, List, Tuple

import numpy as np

from thinfilm.education import (
    LayerSpec,
    build_high_reflector_layers,
    multilayer_rt_spectrum,
    multilayer_rt_spectrum_real_materials,
    quarter_wave_thickness_nm,
)
from thinfilm.materials import material_complex_index


def _make_bragg_layers(periods: int) -> List[LayerSpec]:
    n_high = 2.30 + 0j
    n_low = 1.46 + 0j
    lam0 = 550.0
    d_h = quarter_wave_thickness_nm(lam0, n_high)
    d_l = quarter_wave_thickness_nm(lam0, n_low)
    layers = [LayerSpec("H", n_high, d_h)]
    for _ in range(periods):
        layers.append(LayerSpec("L", n_low, d_l))
        layers.append(LayerSpec("H", n_high, d_h))
    return layers


def benchmark_scalar_tmm(n_wavelengths: int = 600, periods: int = 5) -> Dict[str, float]:
    """Benchmark the scalar TMM kernel."""
    wavelengths = np.linspace(400, 800, n_wavelengths)
    layers = _make_bragg_layers(periods)

    times: List[float] = []
    for _ in range(3):  # 3 runs, take median
        t0 = time.perf_counter()
        result = multilayer_rt_spectrum(
            wavelengths, layers, n_incident=1.0, n_substrate=1.52,
        )
        t1 = time.perf_counter()
        times.append(t1 - t0)

    median_time = sorted(times)[1]
    return {
        "n_wavelengths": n_wavelengths,
        "n_layers": len(layers),
        "n_periods": periods,
        "median_time_s": median_time,
        "throughput_wavelengths_per_s": n_wavelengths / median_time,
    }


def benchmark_dispersive_tmm(n_wavelengths: int = 100) -> Dict[str, float]:
    """Benchmark the dispersive (real-material) TMM."""
    wavelengths = np.linspace(400, 800, n_wavelengths)

    n_mgf2 = float(np.real(material_complex_index("MgF2", 550)))
    n_tio2 = float(np.real(material_complex_index("TiO2", 550)))

    d_l = quarter_wave_thickness_nm(550, n_mgf2)
    d_h = quarter_wave_thickness_nm(550, n_tio2)

    layers = [
        LayerSpec("H", n_tio2, d_h),
        LayerSpec("L", n_mgf2, d_l),
        LayerSpec("H", n_tio2, d_h),
    ]

    material_map = {"n_high": "TiO2", "n_low": "MgF2"}
    role_fallback = {"n_incident": 1.0, "n_substrate": 1.52}

    times: List[float] = []
    for _ in range(3):
        t0 = time.perf_counter()
        result = multilayer_rt_spectrum_real_materials(
            wavelengths, layers,
            design_type="bragg_reflector",
            material_map=material_map,
            role_fallback_indices=role_fallback,
            allow_extrapolate=True,
        )
        t1 = time.perf_counter()
        times.append(t1 - t0)

    median_time = sorted(times)[1]
    return {
        "n_wavelengths": n_wavelengths,
        "n_layers": len(layers),
        "median_time_s": median_time,
        "throughput_wavelengths_per_s": n_wavelengths / median_time,
    }


def main() -> None:
    print("=" * 70)
    print("TMM Performance Baseline")
    print("=" * 70)

    # Scalar TMM benchmarks
    print("\n--- Scalar TMM (constant index) ---")
    for n_wl in [100, 200, 400, 600, 800]:
        for periods in [3, 5, 10]:
            stats = benchmark_scalar_tmm(n_wavelengths=n_wl, periods=periods)
            print(
                f"  N_wl={stats['n_wavelengths']:4d}, "
                f"N_layers={stats['n_layers']:2d}, "
                f"time={stats['median_time_s']:.6f}s, "
                f"throughput={stats['throughput_wavelengths_per_s']:.0f} wl/s"
            )

    # Dispersive TMM benchmarks
    print("\n--- Dispersive TMM (real materials, per-wavelength call) ---")
    for n_wl in [20, 50, 100]:
        stats = benchmark_dispersive_tmm(n_wavelengths=n_wl)
        print(
            f"  N_wl={stats['n_wavelengths']:4d}, "
            f"N_layers={stats['n_layers']:2d}, "
            f"time={stats['median_time_s']:.6f}s, "
            f"throughput={stats['throughput_wavelengths_per_s']:.0f} wl/s"
        )

    print("\n" + "=" * 70)
    print("Baseline complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
