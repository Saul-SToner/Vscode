import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =========================
# 用户配置区
# =========================
COMSOL_CSV = r"C:\Users\L2791\OneDrive\Desktop\TXT.csv"         # 你的 COMSOL 角度扫描文件
EXP_CSV = None             # 实验数据文件；若没有就设为 None
EXP_WAVELENGTH_COL = "wavelength_nm"
EXP_SIGNAL_COL = "signal"

# 你要用 COMSOL 文件中的哪一列作为拟合信号
# 可选："总反射率 (1)" 或 "反射率，端口 1 (1)"
SIGNAL_COLUMN_NAME = "总反射率 (1)"

# 如果实验数据与 COMSOL 波长范围不完全一致，代码会自动取重叠区间
# 是否对每个 theta 自动拟合 y_exp ≈ a*y_sim + b
USE_LINEAR_AB_FIT = True

# 输出目录
OUT_DIR = "theta_scan_output"

# =========================
# 基础工具函数
# =========================
SCI_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?")


def extract_first_scientific_number(token: str) -> float:
    """
    从诸如 '2.361576762846967E0∠0.000000000000000E0°' 中提取前面的实数 2.361576762846967E0。
    """
    token = str(token).strip()
    m = SCI_NUM_RE.search(token)
    if not m:
        raise ValueError(f"无法从 token 中提取数值: {token!r}")
    return float(m.group(0))



def fit_ab(y_exp: np.ndarray, y_model: np.ndarray):
    """
    最小二乘拟合: y_exp ≈ a * y_model + b
    返回 a, b, rmse, y_fit
    """
    y_exp = np.asarray(y_exp, dtype=float).ravel()
    y_model = np.asarray(y_model, dtype=float).ravel()

    X = np.column_stack([y_model, np.ones_like(y_model)])
    beta, *_ = np.linalg.lstsq(X, y_exp, rcond=None)
    a, b = beta
    y_fit = a * y_model + b
    rmse = np.sqrt(np.mean((y_exp - y_fit) ** 2))
    return a, b, rmse, y_fit



def normalized_rmse(y_exp: np.ndarray, y_fit: np.ndarray, eps: float = 1e-12) -> float:
    y_exp = np.asarray(y_exp, dtype=float).ravel()
    y_fit = np.asarray(y_fit, dtype=float).ravel()
    scale = np.max(y_exp) - np.min(y_exp)
    scale = max(scale, eps)
    return np.sqrt(np.mean((y_exp - y_fit) ** 2)) / scale


# =========================
# 读取 COMSOL CSV
# =========================

def read_comsol_angle_scan(csv_path: str, signal_column_name: str = "总反射率 (1)") -> pd.DataFrame:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"找不到 COMSOL CSV 文件: {csv_path}")

    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) < 6:
        raise ValueError("CSV 行数太少，格式不对。")

    header_line = None
    data_start_idx = None
    for i, line in enumerate(lines):
        if line.startswith("% lambda0"):
            header_line = line
            data_start_idx = i + 1
            break
    if header_line is None:
        raise ValueError("没有找到表头行（以 '% lambda0' 开头）。")

    raw_headers = header_line.lstrip("% ").split(",")
    headers = [h.strip() for h in raw_headers]

    if signal_column_name not in headers:
        raise ValueError(
            f"你指定的信号列 {signal_column_name!r} 不在表头里。\n"
            f"当前可用列：{headers}"
        )

    sig_idx = headers.index(signal_column_name)
    lambda_idx = headers.index("lambda0 (m)")
    theta_idx = headers.index("theta (rad)")  # 你的文件里这一列实际上是度
    freq_idx = headers.index("freq (THz)")

    rows = []
    for line in lines[data_start_idx:]:
        if not line.strip() or line.startswith("%"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < len(headers):
            continue

        lambda_m = float(parts[lambda_idx])
        theta_deg = float(parts[theta_idx])  # 注意：你的文件这里实际是“度”，不是弧度
        freq_thz = float(parts[freq_idx])
        signal = extract_first_scientific_number(parts[sig_idx])

        rows.append({
            "lambda_m": lambda_m,
            "lambda_nm": lambda_m * 1e9,
            "theta_deg": theta_deg,
            "freq_thz": freq_thz,
            "signal": signal,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("没有读到有效数据。")

    df = df.sort_values(["lambda_nm", "theta_deg"]).reset_index(drop=True)
    return df


# =========================
# 主流程
# =========================

def main():
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = read_comsol_angle_scan(COMSOL_CSV, SIGNAL_COLUMN_NAME)

    print("=== COMSOL 数据概览 ===")
    print(df.head())
    print()
    print(f"数据点数: {len(df)}")
    print(f"波长个数: {df['lambda_nm'].nunique()}")
    print(f"角度个数: {df['theta_deg'].nunique()}")
    print(f"波长范围: {df['lambda_nm'].min():.3f} ~ {df['lambda_nm'].max():.3f} nm")
    print(f"角度范围: {df['theta_deg'].min():.3f} ~ {df['theta_deg'].max():.3f} deg")
    print(f"signal 最小值: {df['signal'].min():.6g}")
    print(f"signal 最大值: {df['signal'].max():.6g}")

    # 透视成二维矩阵：行=波长，列=角度
    table = df.pivot(index="lambda_nm", columns="theta_deg", values="signal")
    table = table.sort_index().sort_index(axis=1)

    # 导出二维表
    table.to_csv(out_dir / "R_lambda_theta_matrix.csv", encoding="utf-8-sig")

    # 画全部角度的光谱
    plt.figure(figsize=(9, 5.5))
    for theta in table.columns:
        plt.plot(table.index, table[theta].to_numpy(), label=f"{theta:.0f}°")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Signal")
    plt.title(f"COMSOL angle scan: {SIGNAL_COLUMN_NAME}")
    plt.grid(True, alpha=0.3)
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(out_dir / "all_theta_spectra.png", dpi=200)
    plt.close()

    # 热图
    plt.figure(figsize=(8, 5.5))
    X, Y = np.meshgrid(table.columns.to_numpy(), table.index.to_numpy())
    plt.pcolormesh(X, Y, table.to_numpy(), shading="auto")
    plt.xlabel("Theta (deg)")
    plt.ylabel("Wavelength (nm)")
    plt.title(f"Heatmap of {SIGNAL_COLUMN_NAME}")
    plt.colorbar(label="Signal")
    plt.tight_layout()
    plt.savefig(out_dir / "heatmap_lambda_theta.png", dpi=200)
    plt.close()

    # 如果没有实验数据，就到这里
    if EXP_CSV in [None, "", "None"]:
        print("\n未提供实验数据文件，已完成 COMSOL 数据整理和绘图。")
        print(f"输出目录: {out_dir.resolve()}")
        return

    exp_path = Path(EXP_CSV)
    if not exp_path.exists():
        raise FileNotFoundError(f"找不到实验数据文件: {exp_path}")

    exp_df = pd.read_csv(exp_path)
    if EXP_WAVELENGTH_COL not in exp_df.columns or EXP_SIGNAL_COL not in exp_df.columns:
        raise ValueError(
            f"实验数据列名不对。需要列：{EXP_WAVELENGTH_COL!r}, {EXP_SIGNAL_COL!r}\n"
            f"当前列：{list(exp_df.columns)}"
        )

    lam_exp = exp_df[EXP_WAVELENGTH_COL].to_numpy(dtype=float)
    y_exp = exp_df[EXP_SIGNAL_COL].to_numpy(dtype=float)

    # 只保留重叠波长区间
    lam_min = max(lam_exp.min(), table.index.min())
    lam_max = min(lam_exp.max(), table.index.max())
    mask = (lam_exp >= lam_min) & (lam_exp <= lam_max)
    lam_exp_use = lam_exp[mask]
    y_exp_use = y_exp[mask]

    if len(lam_exp_use) < 3:
        raise ValueError("实验数据与 COMSOL 数据重叠的波长点太少。")

    results = []
    best = None

    for theta in table.columns:
        lam_sim = table.index.to_numpy(dtype=float)
        y_sim = table[theta].to_numpy(dtype=float)
        y_sim_interp = np.interp(lam_exp_use, lam_sim, y_sim)

        if USE_LINEAR_AB_FIT:
            a, b, rmse, y_fit = fit_ab(y_exp_use, y_sim_interp)
        else:
            a, b = 1.0, 0.0
            y_fit = y_sim_interp.copy()
            rmse = np.sqrt(np.mean((y_exp_use - y_fit) ** 2))

        nrmse = normalized_rmse(y_exp_use, y_fit)
        rec = {
            "theta_deg": theta,
            "a": a,
            "b": b,
            "rmse": rmse,
            "nrmse": nrmse,
        }
        results.append(rec)

        if best is None or nrmse < best["nrmse"]:
            best = {
                **rec,
                "lam_fit": lam_exp_use.copy(),
                "y_exp": y_exp_use.copy(),
                "y_fit": y_fit.copy(),
                "y_sim_interp": y_sim_interp.copy(),
            }

    res_df = pd.DataFrame(results).sort_values("nrmse").reset_index(drop=True)
    res_df.to_csv(out_dir / "theta_fit_results.csv", index=False, encoding="utf-8-sig")

    print("\n=== 与实验拟合结果（按 nRMSE 排序）===")
    print(res_df.head(10).to_string(index=False))
    print(f"\n最优角度 = {best['theta_deg']:.6f} deg")
    print(f"最优 nRMSE = {best['nrmse']:.6e}")
    print(f"最优 a = {best['a']:.6g}, b = {best['b']:.6g}")

    # 误差-角度曲线
    plt.figure(figsize=(7, 4.5))
    plt.plot(res_df["theta_deg"], res_df["nrmse"], marker="o")
    plt.xlabel("Theta (deg)")
    plt.ylabel("Normalized RMSE")
    plt.title("Error vs Theta")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "error_vs_theta.png", dpi=200)
    plt.close()

    # 最优拟合曲线
    plt.figure(figsize=(8, 5))
    plt.plot(best["lam_fit"], best["y_exp"], label="Experiment")
    plt.plot(best["lam_fit"], best["y_fit"], label=f"Best fit ({best['theta_deg']:.2f}°)")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Signal")
    plt.title("Best theta fit")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "best_theta_fit.png", dpi=200)
    plt.close()

    # 残差
    residual = best["y_exp"] - best["y_fit"]
    plt.figure(figsize=(8, 4.2))
    plt.plot(best["lam_fit"], residual)
    plt.axhline(0, linestyle="--")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Residual")
    plt.title("Residual of best theta fit")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "best_theta_residual.png", dpi=200)
    plt.close()

    print(f"\n输出目录: {out_dir.resolve()}")
    print("已生成：")
    print("- R_lambda_theta_matrix.csv")
    print("- all_theta_spectra.png")
    print("- heatmap_lambda_theta.png")
    print("- theta_fit_results.csv")
    print("- error_vs_theta.png")
    print("- best_theta_fit.png")
    print("- best_theta_residual.png")


if __name__ == "__main__":
    main()
