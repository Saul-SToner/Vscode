"""Laser High-Reflector / Distributed Bragg Reflector (DBR) Design.

Engineering Background:
    Laser cavities require mirrors with extremely high reflectance (>99.9%)
    at the lasing wavelength. DBR mirrors achieve this through quarter-wave
    stack of alternating high/low refractive index materials.

Design Goal:
    Maximize reflectance at 1064 nm (Nd:YAG laser wavelength).

Structure:
    Air / [TiO2/SiO2] x N / SiO2
    Alternating quarter-wave layers of high/low index materials.

Key Metrics:
    - Peak reflectance at 1064 nm
    - Stopband width (R > 99%)
    - Number of layers required
    - Comparison with different material pairs

Teaching Value:
    Demonstrates Bragg reflector physics.
    Shows relationship between index contrast, periods, and reflectance.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from thinfilm.education import (
    LayerSpec,
    build_high_reflector_layers,
    multilayer_rt_spectrum,
)


# ---------------------------------------------------------------------------
# Design parameters
# ---------------------------------------------------------------------------

LAMBDA0_NM = 1064.0  # Nd:YAG laser wavelength
N_AIR = 1.0
N_SIO2 = 1.46
N_TIO2 = 2.30
N_SUBSTRATE = 1.46

PERIODS = 8  # Number of HL pairs


def build_laser_mirror_layers(periods: int = PERIODS) -> list[LayerSpec]:
    """Build laser mirror layer stack."""
    return build_high_reflector_layers(LAMBDA0_NM, N_TIO2, N_SIO2, periods)


def run_laser_mirror(
    wavelengths_nm: np.ndarray | None = None,
    periods: int = PERIODS,
    save_html: bool = False,
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """Run laser mirror simulation.

    Parameters
    ----------
    wavelengths_nm : array, optional
        Wavelength grid. Default: 900-1200 nm, 300 points.
    periods : int
        Number of HL pairs.
    save_html : bool
        If True, save Plotly interactive HTML.
    output_dir : str, optional
        Directory for output files.

    Returns
    -------
    dict
        Contains structure, metrics, wavelengths, R/T/A arrays.
    """
    if wavelengths_nm is None:
        wavelengths_nm = np.linspace(900, 1200, 300)

    layers = build_laser_mirror_layers(periods)

    result = multilayer_rt_spectrum(
        wavelengths_nm,
        layers,
        n_incident=N_AIR,
        n_substrate=N_SUBSTRATE,
        theta0_deg=0.0,
        pol="p",
    )

    R = result["R"]
    T = result["T"]
    A = result["A"]

    # Engineering metrics
    R_peak = float(np.max(R))
    R_at_1064 = float(np.interp(1064, wavelengths_nm, R))

    # Stopband (R > 99%)
    stopband_mask = R > 0.99
    if np.any(stopband_mask):
        stopband_width_nm = float(
            wavelengths_nm[stopband_mask][-1] - wavelengths_nm[stopband_mask][0]
        )
    else:
        stopband_width_nm = 0.0

    # Comparison with different periods
    period_comparison = []
    for n in [3, 5, 8, 10]:
        layers_n = build_laser_mirror_layers(n)
        r_n = multilayer_rt_spectrum(
            [LAMBDA0_NM], layers_n, n_incident=N_AIR, n_substrate=N_SUBSTRATE,
        )["R"][0]
        period_comparison.append({"periods": n, "R_peak": float(r_n)})

    metrics = {
        "peak_reflectance": R_peak,
        "R_at_1064nm": R_at_1064,
        "stopband_width_nm": stopband_width_nm,
        "num_layers": 2 * periods + 1,
        "index_ratio": N_TIO2 / N_SIO2,
        "period_comparison": period_comparison,
    }

    structure = {
        "layers": [
            {"material": "TiO2" if i % 2 == 0 else "SiO2",
             "thickness_nm": LAMBDA0_NM / (4 * (N_TIO2 if i % 2 == 0 else N_SIO2)),
             "n": N_TIO2 if i % 2 == 0 else N_SIO2}
            for i in range(2 * periods)
        ],
        "substrate": "SiO2 (n=1.46)",
        "design_wavelength_nm": LAMBDA0_NM,
        "material_system": "TiO2/SiO2",
    }

    if save_html and output_dir:
        try:
            from thinfilm.plotly_charts import plot_rta_spectrum
            fig = plot_rta_spectrum(
                wavelengths_nm, R, T, A,
                title=f"激光高反镜反射特性 ({periods} periods)",
                design_type=f"TiO2/SiO2 DBR @ {LAMBDA0_NM}nm",
            )
            from pathlib import Path
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(out / "laser_mirror_spectrum.html"))
        except ImportError:
            pass

    return {
        "case_id": "laser_mirror",
        "title": "激光高反镜 / DBR",
        "wavelengths_nm": wavelengths_nm,
        "R": R,
        "T": T,
        "A": A,
        "metrics": metrics,
        "structure": structure,
        "physics": {
            "principle": "布拉格反射：多层膜反射光相长干涉",
            "key_insight": f"折射率比 {N_TIO2}/{N_SIO2}={N_TIO2/N_SIO2:.2f}，{periods} 个周期达到 R>{R_peak*100:.2f}%",
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_laser_mirror(save_html=True, output_dir="outputs/laser_mirror")

    print("=" * 60)
    print("激光高反镜 / DBR 设计")
    print("=" * 60)
    print(f"\n目标波长: {LAMBDA0_NM} nm (Nd:YAG)")
    print(f"膜系结构: Air / [TiO2/SiO2]x{PERIODS} / SiO2")
    print(f"\n关键指标:")
    print(f"  峰值反射率: {result['metrics']['peak_reflectance']:.6f}")
    print(f"  1064nm 处反射率: {result['metrics']['R_at_1064nm']:.6f}")
    print(f"  停带宽度 (R>99%): {result['metrics']['stopband_width_nm']:.1f} nm")
    print(f"  总层数: {result['metrics']['num_layers']}")
    print(f"\n周期数对比:")
    for item in result['metrics']['period_comparison']:
        print(f"    {item['periods']} periods: R = {item['R_peak']:.6f}")
    print(f"\n物理原理: {result['physics']['principle']}")
