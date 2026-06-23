"""Phone Camera Lens Anti-Reflection Coating Design.

Engineering Background:
    Phone camera lenses require broadband anti-reflection coatings to
    minimize ghost images and flare while maximizing light transmission
    across the visible spectrum (400-700 nm).

Design Goal:
    Minimize average reflectance across 400-700 nm on high-index glass.

Structure:
    Air / MgF2 / ZrO2 / SiO2 / LaSFN9 glass
    Multi-layer渐变折射率设计

Key Metrics:
    - Average R across 400-700 nm
    - R at blue (450 nm), green (550 nm), red (650 nm)
    - Transmittance uniformity
    - Comparison with single-layer AR

Teaching Value:
    Demonstrates broadband AR design for real-world applications.
    Shows trade-off between bandwidth and complexity.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from thinfilm.education import LayerSpec, multilayer_rt_spectrum, quarter_wave_thickness_nm


# ---------------------------------------------------------------------------
# Design parameters
# ---------------------------------------------------------------------------

LAMBDA0_NM = 550.0  # Center wavelength
N_AIR = 1.0
N_MGF2 = 1.38  # MgF2 (low)
N_ZRO2 = 2.10  # ZrO2 (mid-high)
N_SIO2 = 1.46  # SiO2 (mid)
N_GLASS = 1.80  # High-index glass (LaSFN9)


def build_phone_lens_ar_layers() -> list[LayerSpec]:
    """Build phone lens AR coating layer stack."""
    d_mgf2 = quarter_wave_thickness_nm(LAMBDA0_NM, N_MGF2)
    d_zro2 = quarter_wave_thickness_nm(LAMBDA0_NM, N_ZRO2)
    d_sio2 = quarter_wave_thickness_nm(LAMBDA0_NM, N_SIO2)
    return [
        LayerSpec("SiO2", N_SIO2, d_sio2),
        LayerSpec("ZrO2", N_ZRO2, d_zro2),
        LayerSpec("MgF2", N_MGF2, d_mgf2),
    ]


def build_single_ar_layers() -> list[LayerSpec]:
    """Single-layer AR for comparison."""
    return [LayerSpec("MgF2", N_MGF2, quarter_wave_thickness_nm(LAMBDA0_NM, N_MGF2))]


def run_phone_lens_ar(
    wavelengths_nm: np.ndarray | None = None,
    save_html: bool = False,
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """Run phone lens AR simulation.

    Parameters
    ----------
    wavelengths_nm : array, optional
        Wavelength grid. Default: 380-780 nm, 200 points.
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
        wavelengths_nm = np.linspace(380, 780, 200)

    # Multi-layer AR
    layers_multi = build_phone_lens_ar_layers()
    result_multi = multilayer_rt_spectrum(
        wavelengths_nm, layers_multi,
        n_incident=N_AIR, n_substrate=N_GLASS,
    )

    # Single-layer AR for comparison
    layers_single = build_single_ar_layers()
    result_single = multilayer_rt_spectrum(
        wavelengths_nm, layers_single,
        n_incident=N_AIR, n_substrate=N_GLASS,
    )

    R_multi = result_multi["R"]
    T_multi = result_multi["T"]
    A_multi = result_multi["A"]

    R_single = result_single["R"]

    # Engineering metrics
    avg_R_multi = float(np.mean(R_multi))
    avg_R_single = float(np.mean(R_single))

    # Color-specific metrics
    R_blue = float(np.interp(450, wavelengths_nm, R_multi))
    R_green = float(np.interp(550, wavelengths_nm, R_multi))
    R_red = float(np.interp(650, wavelengths_nm, R_multi))

    # Color balance (uniformity)
    color_uniformity = 1.0 - (max(R_blue, R_green, R_red) - min(R_blue, R_green, R_red))

    # Transmittance at key wavelengths
    T_blue = float(np.interp(450, wavelengths_nm, T_multi))
    T_green = float(np.interp(550, wavelengths_nm, T_multi))
    T_red = float(np.interp(650, wavelengths_nm, T_multi))
    avg_T_visible = float(np.mean(T_multi))

    metrics = {
        "avg_R_visible": avg_R_multi,
        "avg_R_single_layer": avg_R_single,
        "R_improvement_vs_single": (avg_R_single - avg_R_multi) / avg_R_single * 100,
        "R_blue_450nm": R_blue,
        "R_green_550nm": R_green,
        "R_red_650nm": R_red,
        "color_uniformity": color_uniformity,
        "T_blue": T_blue,
        "T_green": T_green,
        "T_red": T_red,
        "avg_T_visible": avg_T_visible,
    }

    structure = {
        "layers": [
            {"material": "MgF2", "thickness_nm": quarter_wave_thickness_nm(LAMBDA0_NM, N_MGF2), "n": N_MGF2},
            {"material": "ZrO2", "thickness_nm": quarter_wave_thickness_nm(LAMBDA0_NM, N_ZRO2), "n": N_ZRO2},
            {"material": "SiO2", "thickness_nm": quarter_wave_thickness_nm(LAMBDA0_NM, N_SIO2), "n": N_SIO2},
        ],
        "substrate": "LaSFN9 glass (n=1.80)",
        "design_wavelength_nm": LAMBDA0_NM,
    }

    if save_html and output_dir:
        try:
            from thinfilm.plotly_charts import plot_design_comparison
            from pathlib import Path
            designs = {
                "三层 AR": {"wavelength_nm": wavelengths_nm, "R": R_multi},
                "单层 AR": {"wavelength_nm": wavelengths_nm, "R": R_single},
            }
            fig = plot_design_comparison(designs, quantity="R", title="手机镜头 AR 设计对比")
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(out / "phone_lens_ar_comparison.html"))
        except ImportError:
            pass

    return {
        "case_id": "phone_lens_ar",
        "title": "手机镜头多层 AR",
        "wavelengths_nm": wavelengths_nm,
        "R": R_multi,
        "T": T_multi,
        "A": A_multi,
        "R_single_layer": R_single,
        "metrics": metrics,
        "structure": structure,
        "physics": {
            "principle": "多层渐变折射率实现宽带减反",
            "key_insight": "三层 AR 比单层 AR 反射率降低 {:.1f}%".format(
                (avg_R_single - avg_R_multi) / avg_R_single * 100
            ),
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_phone_lens_ar(save_html=True, output_dir="outputs/phone_lens_ar")

    print("=" * 60)
    print("手机镜头多层 AR 设计")
    print("=" * 60)
    print(f"\n膜系结构: Air / MgF2 / ZrO2 / SiO2 / LaSFN9 (n=1.80)")
    print(f"\n关键指标:")
    print(f"  平均反射率 (可见光): {result['metrics']['avg_R_visible']:.4f}")
    print(f"  单层 AR 对比: {result['metrics']['avg_R_single_layer']:.4f}")
    print(f"  改善: {result['metrics']['R_improvement_vs_single']:.1f}%")
    print(f"  R@450nm: {result['metrics']['R_blue_450nm']:.4f}")
    print(f"  R@550nm: {result['metrics']['R_green_550nm']:.4f}")
    print(f"  R@650nm: {result['metrics']['R_red_650nm']:.4f}")
    print(f"  平均透射率: {result['metrics']['avg_T_visible']:.4f}")
    print(f"\n物理原理: {result['physics']['principle']}")
