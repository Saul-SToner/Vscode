from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

from thinfilm import simulate_teaching_case
from thinfilm.io import load_spectrum_csv


def main() -> None:
    font_path = r"C:\Windows\Fonts\msyh.ttc"
    font_prop = FontProperties(fname=font_path)
    plt.rcParams["axes.unicode_minus"] = False

    csv_path = Path(
        r"C:\Users\L2791\OneDrive\Desktop\deg.p\moth_eye_2D_trapezoid_P200_H300_Wtop40_Wbottom180_Glass_550nm_theta0_comsol.csv"
    )
    ref = load_spectrum_csv(csv_path, y_selector="abs(ewfd.S11)^2 (1)")
    wl = np.asarray(ref.x_nm, dtype=float)
    ref_y = np.asarray(ref.y, dtype=float)

    porous = simulate_teaching_case("porous_sio2_layer")
    moth = simulate_teaching_case("moth_eye_effective_gradient")
    porous_y = np.interp(wl, np.asarray(porous["wavelength_nm"], dtype=float), np.asarray(porous["R"], dtype=float))
    moth_y = np.interp(wl, np.asarray(moth["wavelength_nm"], dtype=float), np.asarray(moth["R"], dtype=float))

    lambda0 = 550.0
    ref_at = float(np.interp(lambda0, wl, ref_y))
    porous_at = float(np.interp(lambda0, wl, porous_y))
    moth_at = float(np.interp(lambda0, wl, moth_y))
    mae_por = float(np.mean(np.abs(porous_y - ref_y)))
    mae_moth = float(np.mean(np.abs(moth_y - ref_y)))

    png_out = Path(r"C:\Users\L2791\Downloads\Vscode\moth_eye_vs_porous_cn_fixed.png")
    jpg_out = Path(r"C:\Users\L2791\Downloads\Vscode\moth_eye_vs_porous_cn_fixed.jpg")

    fig, ax = plt.subplots(figsize=(9.5, 5.8), dpi=160)
    ax.set_facecolor("#f7f8fb")
    ax.plot(wl, ref_y, color="#1d4ed8", linewidth=2.2, label="COMSOL 2D 蛾眼梯形结构")
    ax.plot(wl, porous_y, color="#c94f2d", linewidth=2.0, linestyle="--", label="多孔二氧化硅膜层（理论）")
    ax.plot(wl, moth_y, color="#0f766e", linewidth=2.0, linestyle="-.", label="蛾眼等效渐变层（理论）")
    ax.axvline(lambda0, color="#666666", linestyle=":", linewidth=1.2)
    ax.scatter([lambda0] * 3, [ref_at, porous_at, moth_at], color=["#1d4ed8", "#c94f2d", "#0f766e"], s=22, zorder=5)
    ax.set_title("蛾眼 2D 梯形结构与两类等效减反模型对照", fontproperties=font_prop)
    ax.set_xlabel("波长 (nm)", fontproperties=font_prop)
    ax.set_ylabel("反射率 R", fontproperties=font_prop)
    ax.grid(True, alpha=0.35, color="#d7dde5", linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_color("#c9d2dc")
    ax.legend(frameon=True, fontsize=9, prop=font_prop)
    textbox = (
        f"550 nm 处\n"
        f"COMSOL: {ref_at:.4f}\n"
        f"多孔层: {porous_at:.4f}\n"
        f"蛾眼等效: {moth_at:.4f}\n\n"
        f"MAE(多孔): {mae_por:.4e}\n"
        f"MAE(蛾眼): {mae_moth:.4e}"
    )
    ax.text(
        0.985,
        0.98,
        textbox,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        fontproperties=font_prop,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#c9d2dc", alpha=0.96),
    )
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(font_prop)
    fig.tight_layout()
    fig.savefig(png_out, bbox_inches="tight")
    fig.savefig(jpg_out, bbox_inches="tight")
    plt.close(fig)
    print(png_out)
    print(jpg_out)


if __name__ == "__main__":
    main()
