"""Solar Cell Anti-Reflection Coating Design.

Engineering Background:
    Solar cells need to minimize reflection losses across the visible and
    near-infrared spectrum (300-1100 nm) to maximize photon absorption.

Design Goal:
    Minimize average reflectance across 300-1100 nm on silicon substrate.

Structure:
    Air / MgF2 / TiO2 / SiO2 / Si (crystalline silicon)

Key Metrics:
    - Average R across 300-1100 nm
    - R at peak solar wavelength (550 nm)
    - Bandwidth where R < 2%
    - Estimated efficiency improvement vs bare Si

Teaching Value:
    Demonstrates multi-layer AR coating design for broadband applications.
    Shows trade-off between peak performance and bandwidth.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import numpy as np

from thinfilm.education import LayerSpec, multilayer_rt_spectrum, quarter_wave_thickness_nm


# ---------------------------------------------------------------------------
# Design parameters
# ---------------------------------------------------------------------------

# Layer structure: Air / MgF2 / TiO2 / SiO2 / Si
LAMBDA0_NM = 550.0  # Design wavelength
N_AIR = 1.0
N_SIO2 = 1.46
N_MGF2 = 1.38
N_TIO2 = 2.30
N_SI = 3.5 + 0.0j  # Silicon (complex for absorption)

# Layer thicknesses (quarter-wave at design wavelength)
D_MGF2 = quarter_wave_thickness_nm(LAMBDA0_NM, N_MGF2)
D_TIO2 = quarter_wave_thickness_nm(LAMBDA0_NM, N_TIO2)
D_SIO2 = quarter_wave_thickness_nm(LAMBDA0_NM, N_SIO2)


def build_solar_cell_ar_layers() -> list[LayerSpec]:
    """Build the solar cell AR coating layer stack."""
    return [
        LayerSpec("SiO2", N_SIO2, D_SIO2),
        LayerSpec("TiO2", N_TIO2, D_TIO2),
        LayerSpec("MgF2", N_MGF2, D_MGF2),
    ]


def run_solar_cell_ar(
    wavelengths_nm: np.ndarray | None = None,
    save_html: bool = False,
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """Run solar cell AR coating simulation.

    Parameters
    ----------
    wavelengths_nm : array, optional
        Wavelength grid. Default: 300-1100 nm, 200 points.
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
        wavelengths_nm = np.linspace(300, 1100, 200)

    layers = build_solar_cell_ar_layers()

    # Run TMM
    result = multilayer_rt_spectrum(
        wavelengths_nm,
        layers,
        n_incident=N_AIR,
        n_substrate=N_SI,
        theta0_deg=0.0,
        pol="p",
    )

    R = result["R"]
    T = result["T"]
    A = result["A"]

    # Engineering metrics
    avg_R = float(np.mean(R))
    R_at_550 = float(np.interp(550, wavelengths_nm, R))
    bandwidth_mask = R < 0.02
    bandwidth_nm = float(np.sum(bandwidth_mask) * (wavelengths_nm[1] - wavelengths_nm[0]))

    # Bare silicon R for comparison
    r_bare = np.abs((1.0 - N_SI) / (1.0 + N_SI)) ** 2
    R_bare = np.full_like(R, float(r_bare))
    avg_R_bare = float(np.mean(R_bare))

    # Efficiency improvement estimate (simplified)
    # η_improvement ≈ (1 - avg_R) / (1 - avg_R_bare) - 1
    efficiency_improvement = (1.0 - avg_R) / (1.0 - avg_R_bare) - 1.0

    metrics = {
        "avg_R_300_1100nm": avg_R,
        "R_at_550nm": R_at_550,
        "bandwidth_R_lt_2pct_nm": bandwidth_nm,
        "avg_R_bare_Si": avg_R_bare,
        "efficiency_improvement_pct": efficiency_improvement * 100,
        "peak_R": float(np.max(R)),
        "min_R": float(np.min(R)),
        "min_R_wavelength_nm": float(wavelengths_nm[np.argmin(R)]),
    }

    # Structure info
    structure = {
        "layers": [
            {"material": "MgF2", "thickness_nm": D_MGF2, "n": N_MGF2},
            {"material": "TiO2", "thickness_nm": D_TIO2, "n": N_TIO2},
            {"material": "SiO2", "thickness_nm": D_SIO2, "n": N_SIO2},
        ],
        "substrate": "Si (n=3.5)",
        "design_wavelength_nm": LAMBDA0_NM,
    }

    # Save Plotly HTML
    if save_html and output_dir:
        try:
            from thinfilm.plotly_charts import plot_rta_spectrum
            fig = plot_rta_spectrum(
                wavelengths_nm, R, T, A,
                title="太阳能电池减反膜光谱特性",
                design_type="MgF2/TiO2/SiO2/Si 三层 AR",
            )
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(out_path / "solar_cell_ar_spectrum.html"))
        except ImportError:
            pass

    return {
        "case_id": "solar_cell_ar",
        "title": "太阳能电池减反膜",
        "wavelengths_nm": wavelengths_nm,
        "R": R,
        "T": T,
        "A": A,
        "R_bare": R_bare,
        "metrics": metrics,
        "structure": structure,
        "physics": {
            "principle": "多层 1/4 波长膜层相消干涉，拓宽减反带宽",
            "key_insight": "MgF2/TiO2/SiO2 三层渐变折射率实现宽带减反",
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    result = run_solar_cell_ar(save_html=True, output_dir="outputs/solar_cell_ar")

    print("=" * 60)
    print("太阳能电池减反膜设计")
    print("=" * 60)
    print(f"\n膜系结构: Air / MgF2({D_MGF2:.1f}nm) / TiO2({D_TIO2:.1f}nm) / SiO2({D_SIO2:.1f}nm) / Si")
    print(f"\n关键指标:")
    print(f"  平均反射率 (300-1100nm): {result['metrics']['avg_R_300_1100nm']:.4f}")
    print(f"  550nm 处反射率: {result['metrics']['R_at_550nm']:.4f}")
    print(f"  R<2% 带宽: {result['metrics']['bandwidth_R_lt_2pct_nm']:.0f} nm")
    print(f"  效率提升: {result['metrics']['efficiency_improvement_pct']:.1f}%")
    print(f"\n物理原理: {result['physics']['principle']}")
    print(f"\n输出文件: outputs/solar_cell_ar/")
