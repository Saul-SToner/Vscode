"""Smart Window Multi-Layer Coating Design.

Engineering Background:
    Smart windows control solar heat gain by selectively transmitting
    visible light while reflecting near-infrared radiation. This reduces
    air conditioning costs in buildings.

Design Goal:
    Maximize visible transmittance (400-700 nm) while reflecting
    near-infrared (700-2500 nm).

Structure:
    Air / WO3 / NiO / Glass / Ag / Glass
    Electrochromic layers (WO3/NiO) + IR-reflecting Ag layer

Key Metrics:
    - Visible transmittance (T_vis)
    - Solar heat gain coefficient (SHGC)
    - Luminous efficacy
    - NIR rejection ratio

Teaching Value:
    Demonstrates spectrally selective coatings.
    Shows trade-off between visible transparency and IR reflection.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from thinfilm.education import LayerSpec, multilayer_rt_spectrum


# ---------------------------------------------------------------------------
# Design parameters
# ---------------------------------------------------------------------------

N_AIR = 1.0
N_WO3 = 2.10  # Tungsten trioxide (electrochromic)
N_NIO = 2.00  # Nickel oxide (counter electrode)
N_AG = 0.05 + 3.2j  # Silver (complex)
N_GLASS = 1.52
N_SUBSTRATE = 1.52

# Layer thicknesses
D_WO3 = 80.0  # nm
D_NIO = 50.0  # nm
D_AG = 15.0   # nm (thin enough for visible transmission)


def build_smart_window_layers() -> list[LayerSpec]:
    """Build smart window layer stack."""
    return [
        LayerSpec("WO3", N_WO3, D_WO3),
        LayerSpec("NiO", N_NIO, D_NIO),
        LayerSpec("Ag", N_AG, D_AG),
    ]


def run_smart_window(
    wavelengths_nm: np.ndarray | None = None,
    save_html: bool = False,
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """Run smart window simulation.

    Parameters
    ----------
    wavelengths_nm : array, optional
        Wavelength grid. Default: 300-2500 nm, 500 points.
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
        wavelengths_nm = np.linspace(300, 2500, 500)

    layers = build_smart_window_layers()

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
    # Visible band (400-700 nm)
    vis_mask = (wavelengths_nm >= 400) & (wavelengths_nm <= 700)
    T_vis = float(np.mean(T[vis_mask])) if np.any(vis_mask) else 0.0

    # NIR band (700-2500 nm)
    nir_mask = (wavelengths_nm >= 700) & (wavelengths_nm <= 2500)
    T_nir = float(np.mean(T[nir_mask])) if np.any(nir_mask) else 0.0
    R_nir = float(np.mean(R[nir_mask])) if np.any(nir_mask) else 0.0

    # Solar weighted metrics (simplified)
    # Solar spectrum peaks around 500 nm, so weight visible more heavily
    solar_weights = np.exp(-((wavelengths_nm - 500) / 600) ** 2)
    solar_weights /= np.sum(solar_weights)
    T_solar_weighted = float(np.sum(T * solar_weights))
    R_solar_weighted = float(np.sum(R * solar_weights))

    # SHGC (Solar Heat Gain Coefficient) ≈ T_solar + A_solar * 0.5
    A_solar_weighted = float(np.sum(A * solar_weights))
    shgc = T_solar_weighted + A_solar_weighted * 0.5

    # Luminous efficacy (visible transmittance weighted by human eye response)
    # Simplified: just use visible band average
    luminous_efficacy = T_vis

    # NIR rejection ratio
    nir_rejection = T_vis / T_nir if T_nir > 0 else float("inf")

    metrics = {
        "T_visible": T_vis,
        "T_NIR": T_nir,
        "R_NIR": R_nir,
        "T_solar_weighted": T_solar_weighted,
        "R_solar_weighted": R_solar_weighted,
        "SHGC": shgc,
        "luminous_efficacy": luminous_efficacy,
        "NIR_rejection_ratio": nir_rejection,
    }

    structure = {
        "layers": [
            {"material": "WO3", "thickness_nm": D_WO3, "n": N_WO3},
            {"material": "NiO", "thickness_nm": D_NIO, "n": N_NIO},
            {"material": "Ag", "thickness_nm": D_AG, "n": f"{N_AG:.2f}"},
        ],
        "substrate": "Glass (n=1.52)",
        "notes": "电致变色层 (WO3/NiO) + 红外反射层 (Ag)",
    }

    if save_html and output_dir:
        try:
            from thinfilm.plotly_charts import plot_rta_spectrum
            from pathlib import Path
            fig = plot_rta_spectrum(
                wavelengths_nm, R, T, A,
                title="智能窗户光谱特性",
                design_type="WO3/NiO/Ag 电致变色结构",
            )
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            fig.write_html(str(out / "smart_window_spectrum.html"))
        except ImportError:
            pass

    return {
        "case_id": "smart_window",
        "title": "智能窗户多层膜",
        "wavelengths_nm": wavelengths_nm,
        "R": R,
        "T": T,
        "A": A,
        "metrics": metrics,
        "structure": structure,
        "physics": {
            "principle": "薄 Ag 层反射 NIR，电致变色层调节可见光透射",
            "key_insight": f"可见光透过率 {T_vis:.1%}，近红外反射率 {R_nir:.1%}",
        },
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_smart_window(save_html=True, output_dir="outputs/smart_window")

    print("=" * 60)
    print("智能窗户多层膜设计")
    print("=" * 60)
    print(f"\n膜系结构: Air / WO3({D_WO3}nm) / NiO({D_NIO}nm) / Ag({D_AG}nm) / Glass")
    print(f"\n关键指标:")
    print(f"  可见光透过率: {result['metrics']['T_visible']:.1%}")
    print(f"  近红外透过率: {result['metrics']['T_NIR']:.1%}")
    print(f"  近红外反射率: {result['metrics']['R_NIR']:.1%}")
    print(f"  太阳加权透过率: {result['metrics']['T_solar_weighted']:.4f}")
    print(f"  SHGC: {result['metrics']['SHGC']:.4f}")
    print(f"  NIR 抑制比: {result['metrics']['NIR_rejection_ratio']:.1f}x")
    print(f"\n物理原理: {result['physics']['principle']}")
