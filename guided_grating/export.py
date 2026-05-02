from __future__ import annotations

import json
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np

from thinfilm.paths import output_file

from .spectra import summarize_guided_grating_spectrum


def export_guided_grating_result(
    result: Dict[str, Any],
    prefix: str = "guided_grating_demo",
    save_plot: bool = True,
    save_csv: bool = True,
    save_json: bool = True,
    save_txt: bool = True,
) -> Dict[str, str]:
    saved: Dict[str, str] = {}
    sample_id = str(result.get("sample_id") or "guided_grating_case")
    stem = f"{prefix}_{sample_id}"

    wl = np.asarray(result["wavelength_nm"], dtype=float)
    r_vals = np.asarray(result["R"], dtype=float)
    t_vals = np.asarray(result["T"], dtype=float)
    a_vals = np.asarray(result["A"], dtype=float)
    summary = summarize_guided_grating_spectrum(result)

    if save_csv:
        csv_path = output_file(f"{stem}_spectrum.csv")
        with open(csv_path, "w", encoding="utf-8-sig") as f:
            f.write("wavelength_nm,R,T,A\n")
            for row in zip(wl, r_vals, t_vals, a_vals):
                f.write(",".join(f"{float(x):.12g}" for x in row) + "\n")
        saved["csv"] = str(csv_path)

    if save_json:
        json_path = output_file(f"{stem}_summary.json")
        payload = {
            "sample_id": sample_id,
            "model_type": result.get("model_type"),
            "warning": result.get("warning"),
            "spec": result.get("spec", {}),
            "summary": summary,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        saved["json"] = str(json_path)

    if save_txt:
        txt_path = output_file(f"{stem}_summary.txt")
        lines = [
            "Guided Grating Branch Summary",
            "=" * 80,
            f"sample_id              = {sample_id}",
            f"backend                = {result.get('backend')}",
            f"is_placeholder         = {bool(result.get('is_placeholder', False))}",
            f"peak_reflectance       = {summary['peak_reflectance']:.6f}",
            f"peak_wavelength_nm     = {summary['peak_wavelength_nm']:.6f}",
            f"fwhm_nm                = {summary['fwhm_nm']:.6f}",
            f"min_reflectance        = {summary['min_reflectance']:.6f}",
            f"max_transmittance      = {summary['max_transmittance']:.6f}",
            f"max_absorptance        = {summary['max_absorptance']:.6f}",
            f"warning                = {result.get('warning', '')}",
        ]
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        saved["txt"] = str(txt_path)

    if save_plot:
        png_path = output_file(f"{stem}_RTA.png")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(wl, r_vals, label="R", linewidth=2.2, color="#cc3f0c")
        ax.plot(wl, t_vals, label="T", linewidth=2.0, color="#1f77b4")
        ax.plot(wl, a_vals, label="A", linewidth=2.0, color="#2ca02c")
        ax.axvline(summary["peak_wavelength_nm"], linestyle="--", linewidth=1.2, color="#555555", alpha=0.8)
        ax.set_title(f"Guided Grating Demo | {sample_id}")
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Power")
        ax.set_xlim(float(wl[0]), float(wl[-1]))
        ax.set_ylim(0.0, 1.02)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(png_path, dpi=180)
        plt.close(fig)
        saved["png"] = str(png_path)

        main_png = output_file(f"{stem}_main.png")
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.plot(wl, r_vals, linewidth=2.4, color="#cc3f0c")
        ax2.axvline(summary["peak_wavelength_nm"], linestyle="--", linewidth=1.2, color="#555555", alpha=0.8)
        ymin = max(0.0, summary["min_reflectance"] - 0.05)
        ymax = min(1.02, summary["peak_reflectance"] + 0.05)
        if ymax - ymin < 0.08:
            mid = 0.5 * (ymax + ymin)
            ymin = max(0.0, mid - 0.04)
            ymax = min(1.02, mid + 0.04)
        ax2.set_title("Guided Grating Reflectance")
        ax2.set_xlabel("Wavelength (nm)")
        ax2.set_ylabel("R")
        ax2.set_xlim(float(wl[0]), float(wl[-1]))
        ax2.set_ylim(ymin, ymax)
        ax2.grid(True, alpha=0.25)
        fig2.tight_layout()
        fig2.savefig(main_png, dpi=180)
        plt.close(fig2)
        saved["main_png"] = str(main_png)

    return saved
