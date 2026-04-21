
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# User settings
# =========================
COMSOL_CSV = "C:\Users\L2791\OneDrive\Desktop\TXT.csv"   # your COMSOL exported csv
OUTPUT_DIR = "comsol_only_analysis_output"

# Usually COMSOL puts 5 comment/header lines before the real header line.
# If your file format changes, adjust this value.
HEADER_LINE_INDEX = 4  # 0-based index: line 5 is the table header

# Column names in your COMSOL export
LAMBDA_COL = "lambda0 (m)"
THETA_COL = "theta (rad)"     # your file says rad, but values are actually degrees
FREQ_COL = "freq (THz)"
SIGNAL_COL = "总反射率 (1)"    # change this if you want another column

# Optional wavelength window for analysis; set to None to use all
WL_MIN_NM = None
WL_MAX_NM = None


# =========================
# Helpers
# =========================
def parse_comsol_scalar(val):
    """
    Parse COMSOL exported scalar strings like:
        2.361576762846967E0∠0.000000000000000E0°
    and return the magnitude/scalar part:
        2.361576762846967E0
    """
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = s.split("∠")[0].strip()
    if not s:
        return np.nan
    try:
        return float(s)
    except ValueError:
        # fallback: extract scientific notation number
        m = re.search(r'[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?', s)
        if not m:
            return np.nan
        return float(m.group(0))


def load_comsol_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header_line = lines[HEADER_LINE_INDEX].strip().split(",")
    data_lines = lines[HEADER_LINE_INDEX + 1 :]

    rows = []
    for line in data_lines:
        parts = line.rstrip("\n").split(",")
        if len(parts) < len(header_line):
            continue
        row = {header_line[i]: parts[i] for i in range(len(header_line))}
        rows.append(row)

    df = pd.DataFrame(rows)

    # keep only needed columns
    df = df[[LAMBDA_COL, THETA_COL, FREQ_COL, SIGNAL_COL]].copy()

    df[LAMBDA_COL] = pd.to_numeric(df[LAMBDA_COL], errors="coerce")
    df[THETA_COL] = pd.to_numeric(df[THETA_COL], errors="coerce")
    df[FREQ_COL] = pd.to_numeric(df[FREQ_COL], errors="coerce")
    df[SIGNAL_COL] = df[SIGNAL_COL].apply(parse_comsol_scalar)

    df = df.dropna().copy()

    df["lambda_m"] = df[LAMBDA_COL].astype(float)
    df["lambda_nm"] = df["lambda_m"] * 1e9

    # IMPORTANT:
    # Your file header says "theta (rad)", but actual values are 75,76,...,85.
    # These are clearly degrees, so we treat them as degrees directly.
    df["theta_deg"] = df[THETA_COL].astype(float)
    df["freq_thz"] = df[FREQ_COL].astype(float)
    df["signal"] = df[SIGNAL_COL].astype(float)

    if WL_MIN_NM is not None:
        df = df[df["lambda_nm"] >= WL_MIN_NM]
    if WL_MAX_NM is not None:
        df = df[df["lambda_nm"] <= WL_MAX_NM]

    df = df.sort_values(["lambda_nm", "theta_deg"]).reset_index(drop=True)
    return df


def build_matrix(df):
    table = df.pivot(index="lambda_nm", columns="theta_deg", values="signal")
    table = table.sort_index().sort_index(axis=1)
    return table


def compute_peak_valley_table(table):
    results = []
    wl = table.index.to_numpy()

    for theta in table.columns:
        y = table[theta].to_numpy()

        i_min = np.argmin(y)
        i_max = np.argmax(y)

        results.append({
            "theta_deg": float(theta),
            "lambda_at_min_nm": float(wl[i_min]),
            "signal_min": float(y[i_min]),
            "lambda_at_max_nm": float(wl[i_max]),
            "signal_max": float(y[i_max]),
            "signal_mean": float(np.mean(y)),
            "signal_std": float(np.std(y)),
        })

    return pd.DataFrame(results).sort_values("theta_deg").reset_index(drop=True)


def compute_adjacent_theta_sensitivity(table):
    results = []
    thetas = list(table.columns)

    for i in range(len(thetas) - 1):
        t1 = thetas[i]
        t2 = thetas[i + 1]
        y1 = table[t1].to_numpy()
        y2 = table[t2].to_numpy()

        diff = y2 - y1
        rms_diff = float(np.sqrt(np.mean(diff ** 2)))
        mean_abs_diff = float(np.mean(np.abs(diff)))
        max_abs_diff = float(np.max(np.abs(diff)))

        results.append({
            "theta1_deg": float(t1),
            "theta2_deg": float(t2),
            "delta_theta_deg": float(t2 - t1),
            "rms_diff": rms_diff,
            "mean_abs_diff": mean_abs_diff,
            "max_abs_diff": max_abs_diff,
        })

    return pd.DataFrame(results)


def compute_wavelength_sensitivity(table):
    results = []
    thetas = table.columns.to_numpy()
    wl = table.index.to_numpy()

    mat = table.to_numpy()  # shape: (n_lambda, n_theta)

    # across-theta sensitivity at each wavelength
    std_over_theta = np.std(mat, axis=1)
    range_over_theta = np.max(mat, axis=1) - np.min(mat, axis=1)

    # local angular-gradient sensitivity:
    # average adjacent-theta absolute difference for each wavelength
    adj_abs_mean = []
    for i in range(mat.shape[1] - 1):
        adj_abs_mean.append(np.abs(mat[:, i + 1] - mat[:, i]))
    adj_abs_mean = np.mean(np.column_stack(adj_abs_mean), axis=1)

    for i in range(len(wl)):
        results.append({
            "lambda_nm": float(wl[i]),
            "std_over_theta": float(std_over_theta[i]),
            "range_over_theta": float(range_over_theta[i]),
            "adjacent_theta_mean_abs_diff": float(adj_abs_mean[i]),
        })

    res = pd.DataFrame(results).sort_values("lambda_nm").reset_index(drop=True)
    return res


def summarize_best_wavelength_bands(wl_sens_df, top_k=10):
    # rank by across-theta range and adjacent difference
    ranked = wl_sens_df.copy()
    ranked["score"] = (
        ranked["range_over_theta"].rank(method="average", ascending=False)
        + ranked["adjacent_theta_mean_abs_diff"].rank(method="average", ascending=False)
        + ranked["std_over_theta"].rank(method="average", ascending=False)
    )
    ranked = ranked.sort_values("score").reset_index(drop=True)
    return ranked.head(top_k).copy()


def plot_all_theta_spectra(table, out_dir):
    plt.figure(figsize=(9, 5))
    for theta in table.columns:
        plt.plot(table.index, table[theta], label=f"{theta:.0f} deg")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Signal")
    plt.title("Spectra at Different Angles")
    plt.grid(True, alpha=0.3)
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "all_theta_spectra.png", dpi=200)
    plt.close()


def plot_heatmap(table, out_dir):
    plt.figure(figsize=(7, 5))
    plt.imshow(
        table.to_numpy(),
        aspect="auto",
        origin="lower",
        extent=[
            table.columns.min(),
            table.columns.max(),
            table.index.min(),
            table.index.max(),
        ],
    )
    plt.colorbar(label="Signal")
    plt.xlabel("Theta (deg)")
    plt.ylabel("Wavelength (nm)")
    plt.title("Signal(lambda, theta)")
    plt.tight_layout()
    plt.savefig(out_dir / "heatmap_lambda_theta.png", dpi=200)
    plt.close()


def plot_adjacent_theta_sensitivity(df_sens, out_dir):
    x = [f"{r.theta1_deg:.0f}->{r.theta2_deg:.0f}" for _, r in df_sens.iterrows()]
    y = df_sens["rms_diff"].to_numpy()

    plt.figure(figsize=(8, 4.5))
    plt.plot(range(len(y)), y, marker="o")
    plt.xticks(range(len(x)), x, rotation=45)
    plt.xlabel("Adjacent angle pair")
    plt.ylabel("RMS spectral difference")
    plt.title("Adjacent-Angle Sensitivity")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "adjacent_theta_sensitivity.png", dpi=200)
    plt.close()


def plot_wavelength_sensitivity(wl_sens_df, out_dir):
    plt.figure(figsize=(8, 4.8))
    plt.plot(wl_sens_df["lambda_nm"], wl_sens_df["range_over_theta"], label="Range over theta")
    plt.plot(wl_sens_df["lambda_nm"], wl_sens_df["adjacent_theta_mean_abs_diff"], label="Adj-theta mean abs diff")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Sensitivity")
    plt.title("Wavelength Sensitivity")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "wavelength_sensitivity.png", dpi=200)
    plt.close()


def main():
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_comsol_csv(COMSOL_CSV)

    print("=== COMSOL data overview ===")
    print(df[["lambda_m", "lambda_nm", "theta_deg", "freq_thz", "signal"]].head())
    print()
    print(f"Data points: {len(df)}")
    print(f"Number of wavelengths: {df['lambda_nm'].nunique()}")
    print(f"Number of angles: {df['theta_deg'].nunique()}")
    print(f"Wavelength range: {df['lambda_nm'].min():.3f} ~ {df['lambda_nm'].max():.3f} nm")
    print(f"Angle range: {df['theta_deg'].min():.3f} ~ {df['theta_deg'].max():.3f} deg")
    print(f"Signal min: {df['signal'].min():.8g}")
    print(f"Signal max: {df['signal'].max():.8g}")
    print()

    table = build_matrix(df)
    table.to_csv(out_dir / "signal_lambda_theta_matrix.csv", encoding="utf-8-sig")

    peak_valley_df = compute_peak_valley_table(table)
    peak_valley_df.to_csv(out_dir / "peak_valley_by_theta.csv", index=False, encoding="utf-8-sig")

    adj_sens_df = compute_adjacent_theta_sensitivity(table)
    adj_sens_df.to_csv(out_dir / "adjacent_theta_sensitivity.csv", index=False, encoding="utf-8-sig")

    wl_sens_df = compute_wavelength_sensitivity(table)
    wl_sens_df.to_csv(out_dir / "wavelength_sensitivity.csv", index=False, encoding="utf-8-sig")

    top_wl_df = summarize_best_wavelength_bands(wl_sens_df, top_k=10)
    top_wl_df.to_csv(out_dir / "top10_sensitive_wavelengths.csv", index=False, encoding="utf-8-sig")

    plot_all_theta_spectra(table, out_dir)
    plot_heatmap(table, out_dir)
    plot_adjacent_theta_sensitivity(adj_sens_df, out_dir)
    plot_wavelength_sensitivity(wl_sens_df, out_dir)

    print("=== Peak/valley summary by theta ===")
    print(peak_valley_df.to_string(index=False))
    print()

    print("=== Adjacent-theta sensitivity ===")
    print(adj_sens_df.to_string(index=False))
    print()

    print("=== Top 10 most sensitive wavelengths ===")
    print(top_wl_df.to_string(index=False))
    print()

    print("Done.")
    print(f"Output folder: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
