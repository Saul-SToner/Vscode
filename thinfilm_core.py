from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar


# =========================================================
# 0. 运行模式
# =========================================================
# 可选:
#   "preview_csv"                 -> 直接预览单个 CSV（适合 COMSOL 原始导出）
#   "export_clean_csv"            -> 把 COMSOL 原始 CSV 清洗成标准两列 CSV
#   "fit_csv"                     -> 用两条反射率 CSV 做双角度拟合
#   "fit_csv_with_theta2_search"  -> 用两条反射率 CSV 做双角度拟合，并联合搜索第二角
#   "batch_fit_csv"               -> 批量处理文件夹中的成对反射率 CSV
#   "batch_error_analysis"        -> 批量拟合并输出真实厚度误差统计
#   "single_sample_error_analysis"-> 单一样品误差来源分析
#   "theta2_scan_at_fixed_d"      -> 固定厚度，只扫描第二角并比较曲线
#   "fit_csv_compare_pols"   -> 固定厚度下比较指定角度曲线与理论 s/p/avg
#   "single_angle_0deg_scan"      -> 只用 0deg 曲线做厚度扫描
#   "objective_heatmap_d_theta2"  -> 画 objective(d, theta2) 热图

RUN_MODE = "fit_csv_with_theta2_search"

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

CSV_FILE_0DEG = DATA_DIR / "deg.s" / "60nm_10deg_s.csv"
CSV_FILE_2DEG = DATA_DIR / "deg.s" / "60nm_80deg_s.csv"

FIT_Y_SELECTOR_0DEG = "总反射率"
FIT_Y_SELECTOR_2DEG = "总反射率"

N0 = 1.0
N1 = 1.38
N2 = 1.52
USE_DISPERSION = False
DISPERSION_FORM = "cauchy_um"
N1_DISPERSION_B = 0.0
N1_DISPERSION_C = 0.0
N2_DISPERSION_B = 0.0
N2_DISPERSION_C = 0.0

POL = "s"
THETA1 = 10.0
THETA2 = 80.0
THETA2_SEARCH_MIN = -1.0
THETA2_SEARCH_MAX = 1.0
THETA2_SEARCH_STEP = 0.1
MIX_P_WEIGHT = 0.5
FIT_MIX_WEIGHT = False
MIX_WEIGHT_SEARCH_MIN = 0.0
MIX_WEIGHT_SEARCH_MAX = 1.0
MIX_WEIGHT_SEARCH_STEP = 0.05
MIX_USE_ENDPOINT_TARGET_BLEND = True
MIX_SOURCE_P_WEIGHT = 0.6
MIX_SOURCE_0DEG_MODE = "s"
MIX_SOURCE_2DEG_MODE = "blend"
MIX_SOURCE_CSV_0DEG_S: Optional[Path] = DATA_DIR / "deg.s" / "60nm_10deg_s.csv"
MIX_SOURCE_CSV_0DEG_P: Optional[Path] = DATA_DIR / "deg.p" / "60nm_10deg_p.csv"
MIX_SOURCE_CSV_2DEG_S: Optional[Path] = DATA_DIR / "deg.s" / "60nm_80deg_s.csv"
MIX_SOURCE_CSV_2DEG_P: Optional[Path] = DATA_DIR / "deg.p" / "60nm_80deg_p.csv"

# Generic two-angle aliases for future 10deg/80deg workflows.
CSV_FILE_ANGLE1 = CSV_FILE_0DEG
CSV_FILE_ANGLE2 = CSV_FILE_2DEG
FIT_Y_SELECTOR_ANGLE1 = FIT_Y_SELECTOR_0DEG
FIT_Y_SELECTOR_ANGLE2 = FIT_Y_SELECTOR_2DEG
MIX_SOURCE_ANGLE1_MODE = MIX_SOURCE_0DEG_MODE
MIX_SOURCE_ANGLE2_MODE = MIX_SOURCE_2DEG_MODE
MIX_SOURCE_CSV_ANGLE1_S = MIX_SOURCE_CSV_0DEG_S
MIX_SOURCE_CSV_ANGLE1_P = MIX_SOURCE_CSV_0DEG_P
MIX_SOURCE_CSV_ANGLE2_S = MIX_SOURCE_CSV_2DEG_S
MIX_SOURCE_CSV_ANGLE2_P = MIX_SOURCE_CSV_2DEG_P

D_MIN = 5e-9
D_MAX = 300e-9
N_GRID = 1500
N_ITER = 1

LAMBDA_A = 1e6
LAMBDA_B = 1e6

LAMBDA_MIN_NM = 400.0
LAMBDA_MAX_NM = 800.0
N_LAMBDA = 300

USE_THICKNESS_CALIBRATION = False
CAL_A = 1.0
CAL_B = 0.0

SEARCH_METHOD = "multiscale_shape"
OBJECTIVE_SMOOTH_WINDOW = 9
OBJECTIVE_WEIGHT_LEVEL = 0.10
OBJECTIVE_WEIGHT_SHAPE = 0.30
OBJECTIVE_WEIGHT_SLOPE = 0.60

SEARCH_COARSE_D_STEP_NM = 1.0
SEARCH_COARSE_THETA_STEP_DEG = 0.1
SEARCH_TOP_K = 4
SEARCH_MIN_D_SEPARATION_NM = 4.0
SEARCH_MIN_THETA_SEPARATION_DEG = 0.08

REFINE_D_WINDOWS_NM = (8.0, 2.0, 0.5)
REFINE_THETA_WINDOWS_DEG = (0.35, 0.10, 0.025)
REFINE_D_GRID_POINTS = 81
REFINE_THETA_GRID_POINTS = 61
REFINE_COORDINATE_CYCLES = 2


# =========================================================
# 1. 路径配置
# =========================================================
OUTPUT_DIR = Path(r"C:\Users\L2791\thinfilm_outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def sync_angle_config_aliases() -> None:
    global CSV_FILE_0DEG, CSV_FILE_2DEG
    global FIT_Y_SELECTOR_0DEG, FIT_Y_SELECTOR_2DEG
    global MIX_SOURCE_0DEG_MODE, MIX_SOURCE_2DEG_MODE
    global MIX_SOURCE_CSV_0DEG_S, MIX_SOURCE_CSV_0DEG_P
    global MIX_SOURCE_CSV_2DEG_S, MIX_SOURCE_CSV_2DEG_P

    CSV_FILE_0DEG = CSV_FILE_ANGLE1
    CSV_FILE_2DEG = CSV_FILE_ANGLE2
    FIT_Y_SELECTOR_0DEG = FIT_Y_SELECTOR_ANGLE1
    FIT_Y_SELECTOR_2DEG = FIT_Y_SELECTOR_ANGLE2
    MIX_SOURCE_0DEG_MODE = MIX_SOURCE_ANGLE1_MODE
    MIX_SOURCE_2DEG_MODE = MIX_SOURCE_ANGLE2_MODE
    MIX_SOURCE_CSV_0DEG_S = MIX_SOURCE_CSV_ANGLE1_S
    MIX_SOURCE_CSV_0DEG_P = MIX_SOURCE_CSV_ANGLE1_P
    MIX_SOURCE_CSV_2DEG_S = MIX_SOURCE_CSV_ANGLE2_S
    MIX_SOURCE_CSV_2DEG_P = MIX_SOURCE_CSV_ANGLE2_P


def format_angle_label(theta_deg: float) -> str:
    rounded = round(float(theta_deg), 6)
    if abs(rounded - round(rounded)) < 1e-6:
        return f"{int(round(rounded))}deg"
    return f"{rounded:g}deg"

# ---------- 其它模式默认参数（防止切换 RUN_MODE 时 NameError） ----------
PREVIEW_CSV_FILE = CSV_FILE_2DEG
PREVIEW_Y_SELECTOR: Optional[Union[int, str]] = FIT_Y_SELECTOR_2DEG

EXPORT_CLEAN_INPUT_FILE = CSV_FILE_2DEG
EXPORT_CLEAN_OUTPUT_FILE = OUTPUT_DIR / "clean_export.csv"
EXPORT_Y_SELECTOR: Optional[Union[int, str]] = FIT_Y_SELECTOR_2DEG

FIXED_D_COMPARE_NM = 90.0
FIXED_THETA_COMPARE_DEG = 80.0

THETA2_SCAN_FIXED_D_NM = 90.0
THETA2_SCAN_MIN_DEG = 70.0
THETA2_SCAN_MAX_DEG = 90.0
THETA2_SCAN_STEP_DEG = 0.1
THETA2_SCAN_POL = "p"

BATCH_INPUT_DIR = Path(r"C:\Users\L2791\generated_batch_csv")
BATCH_LABEL_1 = "0deg"
BATCH_LABEL_2 = "80deg_p"
TRUE_THICKNESS_REGEX = r"(\d+(?:\.\d+)?)\s*nm"
TRUE_THICKNESS_FALLBACK_FIRST_NUMBER = True

SINGLE_SAMPLE_TRUE_THICKNESS_NM: Optional[float] = None
SINGLE_SAMPLE_REPORT_ID = "single_case"
SINGLE_SAMPLE_THETA2_HALF_RANGE_DEG = 0.08
SINGLE_SAMPLE_THETA2_STEP_DEG = 0.002
SINGLE_SAMPLE_N1_RELATIVE_HALF_RANGE = 0.03
SINGLE_SAMPLE_N2_RELATIVE_HALF_RANGE = 0.03
SINGLE_SAMPLE_N_SCAN_POINTS = 31
POL_COMPARE_LIST = ("s", "p", "avg", "mix")
POL_COMPARE_REPORT_ID = "single_case_pol_compare"


# =========================================================
# 4. 数据结构
# =========================================================
@dataclass
class SpectrumData:
    path: Path
    x_nm: np.ndarray
    y: np.ndarray
    x_label: str
    y_label: str
    y_kind: str
    data_table: pd.DataFrame
    comment_lines: List[str]
    all_column_labels: List[str]


# =========================================================
# 5. 文件工具
# =========================================================
def save_text_report(filename: str, lines: List[str]) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(str(line) + "\n")
    print(f"Saved report: {path}")


def save_json_report(filename: str, payload: Dict) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved json: {path}")


def save_rows_csv(filename: str, header: List[str], rows: List[List]) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        for row in rows:
            f.write(",".join(str(x) for x in row) + "\n")
    print(f"Saved csv: {path}")


def calibrate_thickness_nm(
    d_fit_nm: float,
    use_calibration: bool = True,
    a: float = 1.0,
    b: float = 0.0,
) -> float:
    if use_calibration:
        return a * d_fit_nm + b
    return d_fit_nm


def _read_text_with_fallback(path: Path) -> str:
    """
    按多个常见编码尝试读取文本文件。
    """
    encodings = ["utf-8-sig", "utf-8", "gbk", "cp936", "ansi", "latin1"]

    last_error = None
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except Exception as e:
            last_error = e

    raise UnicodeDecodeError(
        "fallback",
        b"",
        0,
        1,
        f"无法用常见编码读取文件: {path}. 最后错误: {last_error}",
    )


def _read_csv_with_fallback(path: Path, **kwargs) -> pd.DataFrame:
    """
    按多个常见编码尝试 pandas.read_csv。
    """
    encodings = ["utf-8-sig", "utf-8", "gbk", "cp936", "latin1"]

    last_error = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except Exception as e:
            last_error = e

    raise ValueError(f"无法用常见编码读取 CSV: {path}. 最后错误: {last_error}")


# =========================================================
# 6. CSV 读取：兼容标准 CSV + COMSOL 原始导出 CSV + 多列选择
# =========================================================
def _read_text_lines(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    return _read_text_with_fallback(path).splitlines()


def _extract_comment_lines(lines: Sequence[str]) -> List[str]:
    return [line.strip() for line in lines if line.strip().startswith("%")]


def _extract_header_candidates_from_comments(comment_lines: Sequence[str]) -> List[str]:
    """
    尝试从 COMSOL 注释头中提取最后一行列标题。
    常见格式:
        % lambda0 (m),freq (THz),反射率，端口 1 (1)
        % lambda0 (m),R_0deg,R_80deg
    """
    for line in reversed(comment_lines):
        text = line.lstrip("%").strip()
        parts = [p.strip().strip('"') for p in text.split(",")]
        if len(parts) >= 2:
            joined = ",".join(parts).lower()
            looks_like_header = any(
                key in joined
                for key in [
                    "lambda", "wavelength", "freq", "reflect", "thz",
                    "(m)", "nm", "intensity", "trans", "abs(", "反射"
                ]
            )
            if looks_like_header:
                return parts
    return []


def _normalize_label(label: str) -> str:
    return label.strip().strip('"').lower()


def _guess_y_kind(y_label: str, y_values: np.ndarray) -> str:
    label = _normalize_label(y_label)

    if "reflect" in label or "反射" in label or label in {"r", "refl"}:
        return "reflectance"
    if "freq" in label or "thz" in label or "hz" in label:
        return "frequency"
    if "trans" in label or "透射" in label:
        return "transmittance"

    y_min = float(np.nanmin(y_values))
    y_max = float(np.nanmax(y_values))

    if y_min >= -0.05 and y_max <= 1.2:
        return "reflectance"
    if y_max > 10:
        return "frequency"
    return "unknown"


def _convert_x_to_nm(x_values: np.ndarray, x_label: str) -> np.ndarray:
    label = _normalize_label(x_label)

    if "nm" in label:
        return x_values.astype(float)

    if "(m)" in label or label.endswith("_m") or "lambda0" in label or "wavelength" in label:
        if np.nanmax(np.abs(x_values)) < 1e-3:
            return x_values.astype(float) * 1e9

    if np.nanmax(np.abs(x_values)) < 1e-3:
        return x_values.astype(float) * 1e9

    return x_values.astype(float)


def _pick_column_index(
    labels: Sequence[str],
    selector: Optional[Union[int, str]],
    default_index: int = 1,
) -> int:
    n_cols = len(labels)
    if n_cols < 2:
        raise ValueError("数据列数不足。")

    if selector is None:
        return min(default_index, n_cols - 1)

    if isinstance(selector, int):
        if selector < 0 or selector >= n_cols:
            raise IndexError(f"列号越界: selector={selector}, n_cols={n_cols}")
        return selector

    key = _normalize_label(selector)
    for i, lab in enumerate(labels):
        if key in _normalize_label(lab):
            return i

    raise ValueError(f"没有找到匹配列: selector='{selector}', labels={list(labels)}")


def _parse_comsol_value(value) -> float:
    if value is None:
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()
    if text == "":
        return np.nan

    try:
        return float(text)
    except Exception:
        pass

    if "∠" in text:
        try:
            mag_text, ang_text = text.split("∠", 1)
            mag = float(mag_text.strip())
            ang_text = ang_text.strip().replace("°", "")
            ang_deg = float(ang_text)
            real = mag * np.cos(np.deg2rad(ang_deg))
            imag = mag * np.sin(np.deg2rad(ang_deg))
            return float(np.hypot(real, imag))
        except Exception:
            pass

    text_complex = text.replace("i", "j").replace("I", "j")
    try:
        c = complex(text_complex)
        return float(abs(c))
    except Exception:
        pass

    return np.nan


def _clean_numeric_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    兼容不同 pandas 版本：
    - 新版本优先用 DataFrame.map
    - 老版本回退到 DataFrame.applymap
    """
    try:
        df_num = df.map(_parse_comsol_value)
    except AttributeError:
        df_num = df.applymap(_parse_comsol_value)

    df_num = df_num.dropna(how="all")
    return df_num


def _load_standard_csv_with_headers(path: Path) -> Optional[Tuple[pd.DataFrame, List[str]]]:
    try:
        df = _read_csv_with_fallback(path)
    except Exception:
        return None

    if df.shape[1] < 2:
        return None

    df_num = _clean_numeric_dataframe(df)
    if df_num.shape[1] < 2 or len(df_num) < 2:
        return None

    labels = [str(c).strip() for c in df.columns]
    return df_num.reset_index(drop=True), labels


def _load_comsol_numeric_table(path: Path, comment_lines: Sequence[str]) -> Tuple[pd.DataFrame, List[str]]:
    df = _read_csv_with_fallback(path, comment="%", header=None)
    df_num = _clean_numeric_dataframe(df)

    if df_num.shape[1] < 2 or len(df_num) < 2:
        raise ValueError(f"CSV 至少需要两列有效数值数据: {path}")

    header_candidates = _extract_header_candidates_from_comments(comment_lines)

    if len(header_candidates) >= df_num.shape[1]:
        labels = header_candidates[:df_num.shape[1]]
    else:
        labels = []
        for i in range(df_num.shape[1]):
            if i < len(header_candidates):
                labels.append(header_candidates[i])
            else:
                labels.append(f"col_{i}")

    return df_num.reset_index(drop=True), labels


def load_spectrum_csv(
    path: Path,
    y_selector: Optional[Union[int, str]] = None,
    x_selector: Union[int, str] = 0,
) -> SpectrumData:
    """
    通用读取：
    1) 标准 CSV:
         wavelength_nm,reflectance
         400,0.12
         ...
    2) COMSOL 原始导出:
         % Model,...
         % lambda0 (m),freq (THz),反射率，端口 1 (1)
         4.0e-7,749.4,1.685E-2∠0°
         ...
    3) 多列数值表:
         % lambda0 (m),R_0deg,R_80deg
         ...
       通过 y_selector 指定要用哪一列。
    """
    path = Path(path)
    lines = _read_text_lines(path)
    comment_lines = _extract_comment_lines(lines)

    std_result = _load_standard_csv_with_headers(path)
    if std_result is not None:
        data_table, labels = std_result
    else:
        data_table, labels = _load_comsol_numeric_table(path, comment_lines)

    x_idx = _pick_column_index(labels, x_selector, default_index=0)
    y_idx = _pick_column_index(labels, y_selector, default_index=1)

    x_label = labels[x_idx]
    y_label = labels[y_idx]

    x = data_table.iloc[:, x_idx].to_numpy(dtype=float)
    y = data_table.iloc[:, y_idx].to_numpy(dtype=float)

    valid = np.isfinite(x) & np.isfinite(y)
    x = x[valid]
    y = y[valid]

    if len(x) < 2:
        raise ValueError(f"有效数值点不足: {path}")

    x_nm = _convert_x_to_nm(x, x_label)
    y_kind = _guess_y_kind(y_label, y)

    return SpectrumData(
        path=path,
        x_nm=x_nm,
        y=y.astype(float),
        x_label=x_label,
        y_label=y_label,
        y_kind=y_kind,
        data_table=data_table.copy(),
        comment_lines=list(comment_lines),
        all_column_labels=list(labels),
    )


def read_reflectance_csv(
    path: Path,
    y_selector: Optional[Union[int, str]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    spec = load_spectrum_csv(path, y_selector=y_selector)

    if spec.y_kind != "reflectance":
        raise ValueError(
            f"文件 {path} 的目标列不是反射率。\n"
            f"检测到 y_label = '{spec.y_label}', y_kind = '{spec.y_kind}'.\n"
            f"如果是多列表，请设置正确的 y_selector；"
            f"如果当前列是 freq/THz，则它不能直接用于膜厚拟合。"
        )

    y_min = float(np.nanmin(spec.y))
    y_max = float(np.nanmax(spec.y))
    if y_min < -0.1 or y_max > 1.5:
        raise ValueError(
            f"文件 {path} 的反射率范围异常: [{y_min:.6f}, {y_max:.6f}]。"
        )

    return spec.x_nm, spec.y


def load_reflectance_spec(
    path: Path,
    y_selector: Optional[Union[int, str]] = None,
) -> SpectrumData:
    spec = load_spectrum_csv(path, y_selector=y_selector)

    if spec.y_kind != "reflectance":
        raise ValueError(
            f"File {path} does not contain a reflectance column for fitting. "
            f"Detected y_label='{spec.y_label}', y_kind='{spec.y_kind}'."
        )

    y_min = float(np.nanmin(spec.y))
    y_max = float(np.nanmax(spec.y))
    if y_min < -0.1 or y_max > 1.5:
        raise ValueError(
            f"File {path} has an invalid reflectance range: [{y_min:.6f}, {y_max:.6f}]."
        )

    return spec


def validate_single_fit_input_theta(
    spec: SpectrumData,
    expected_theta_deg: float,
) -> None:
    theta_deg = extract_constant_theta_deg(spec)
    if theta_deg is not None and abs(theta_deg - expected_theta_deg) > 0.5:
        raise ValueError(
            f"Input angle mismatch for {spec.path.name}: expected about "
            f"{expected_theta_deg:.3f} deg, but the CSV theta column is {theta_deg:.3f} deg."
        )


def extract_constant_theta_deg(spec: SpectrumData) -> Optional[float]:
    for idx, label in enumerate(spec.all_column_labels):
        norm_label = _normalize_label(label)
        if "theta" not in norm_label:
            continue

        values = spec.data_table.iloc[:, idx].to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        if len(values) == 0:
            continue

        value_span = float(np.max(values) - np.min(values))
        value_mid = float(np.median(values))
        if value_span > 1e-6:
            continue

        if np.max(np.abs(values)) <= 2.5 * np.pi:
            return float(np.rad2deg(value_mid))
        return value_mid

    return None


def validate_dual_fit_inputs(
    spec_1: SpectrumData,
    expected_theta_1_deg: float,
    spec_2: SpectrumData,
    expected_theta_2_deg: float,
) -> None:
    validate_single_fit_input_theta(spec_1, expected_theta_1_deg)
    validate_single_fit_input_theta(spec_2, expected_theta_2_deg)

    common_min = max(float(np.min(spec_1.x_nm)), float(np.min(spec_2.x_nm)), LAMBDA_MIN_NM)
    common_max = min(float(np.max(spec_1.x_nm)), float(np.max(spec_2.x_nm)), LAMBDA_MAX_NM)
    if common_max <= common_min:
        return

    grid_nm = np.linspace(common_min, common_max, 200)
    y1 = np.interp(grid_nm, spec_1.x_nm, spec_1.y)
    y2 = np.interp(grid_nm, spec_2.x_nm, spec_2.y)

    rms_diff = float(np.sqrt(np.mean((y1 - y2) ** 2)))
    corr = float(np.corrcoef(y1, y2)[0, 1]) if len(y1) >= 2 else 1.0
    if rms_diff < 1e-5 and corr > 0.9999:
        raise ValueError(
            f"The two fit inputs are nearly identical over {common_min:.1f}-{common_max:.1f} nm "
            f"(RMS diff={rms_diff:.3e}, corr={corr:.6f}). Dual-angle fitting will collapse in this case."
        )


def build_endpoint_blend_curve(
    spec_s: SpectrumData,
    spec_p: SpectrumData,
    source_mode: str,
    mix_p_weight: float,
) -> Tuple[np.ndarray, np.ndarray, str]:
    mode = str(source_mode).strip().lower()
    if mode == "s":
        return spec_s.x_nm, spec_s.y, f"s:{spec_s.path.name}"
    if mode == "p":
        return spec_p.x_nm, spec_p.y, f"p:{spec_p.path.name}"
    if mode != "blend":
        raise ValueError(
            f"Unsupported mixed-source mode '{source_mode}'. Use 's', 'p', or 'blend'."
        )

    blend_weight = float(np.clip(mix_p_weight, 0.0, 1.0))
    grid_nm, Rs_i, Rp_i = unify_two_reflectance_curves(
        spec_s.x_nm,
        spec_s.y,
        spec_p.x_nm,
        spec_p.y,
        wmin_nm=LAMBDA_MIN_NM,
        wmax_nm=LAMBDA_MAX_NM,
        n_lambda=max(len(spec_s.x_nm), len(spec_p.x_nm), N_LAMBDA),
    )
    R_mix = blend_weight * Rp_i + (1.0 - blend_weight) * Rs_i
    source_desc = (
        f"blend(eta_p={blend_weight:.6f}):"
        f"{spec_p.path.name}+{spec_s.path.name}"
    )
    return grid_nm, R_mix, source_desc


def resolve_dual_fit_curves(
    csv_file_1: Path,
    csv_file_2: Path,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Union[str, float]]]:
    if POL == "mix" and MIX_USE_ENDPOINT_TARGET_BLEND:
        required_paths = {
            "0deg_s": MIX_SOURCE_CSV_0DEG_S,
            "0deg_p": MIX_SOURCE_CSV_0DEG_P,
            "2deg_s": MIX_SOURCE_CSV_2DEG_S,
            "2deg_p": MIX_SOURCE_CSV_2DEG_P,
        }
        missing = [name for name, path in required_paths.items() if path is None]
        if missing:
            raise ValueError(
                "Mixed endpoint blending is enabled, but these source CSV paths are missing: "
                + ", ".join(missing)
            )

        spec_0_s = load_reflectance_spec(Path(MIX_SOURCE_CSV_0DEG_S), y_selector=FIT_Y_SELECTOR_0DEG)
        spec_0_p = load_reflectance_spec(Path(MIX_SOURCE_CSV_0DEG_P), y_selector=FIT_Y_SELECTOR_0DEG)
        spec_2_s = load_reflectance_spec(Path(MIX_SOURCE_CSV_2DEG_S), y_selector=FIT_Y_SELECTOR_2DEG)
        spec_2_p = load_reflectance_spec(Path(MIX_SOURCE_CSV_2DEG_P), y_selector=FIT_Y_SELECTOR_2DEG)

        validate_single_fit_input_theta(spec_0_s, THETA1)
        validate_single_fit_input_theta(spec_0_p, THETA1)
        validate_single_fit_input_theta(spec_2_s, THETA2)
        validate_single_fit_input_theta(spec_2_p, THETA2)

        w1_nm, R1, source_1 = build_endpoint_blend_curve(
            spec_0_s, spec_0_p, MIX_SOURCE_0DEG_MODE, MIX_SOURCE_P_WEIGHT
        )
        w2_nm, R2, source_2 = build_endpoint_blend_curve(
            spec_2_s, spec_2_p, MIX_SOURCE_2DEG_MODE, MIX_SOURCE_P_WEIGHT
        )

        lam_nm, R1_i, R2_i = unify_two_reflectance_curves(
            w1_nm,
            R1,
            w2_nm,
            R2,
            wmin_nm=LAMBDA_MIN_NM,
            wmax_nm=LAMBDA_MAX_NM,
            n_lambda=N_LAMBDA,
        )
        meta: Dict[str, Union[str, float]] = {
            "input_mode": "mix_endpoint_target_blend",
            "curve_1_source": source_1,
            "curve_2_source": source_2,
            "mix_source_p_weight": float(MIX_SOURCE_P_WEIGHT),
            "mix_source_0deg_mode": str(MIX_SOURCE_0DEG_MODE),
            "mix_source_2deg_mode": str(MIX_SOURCE_2DEG_MODE),
        }
        return lam_nm, R1_i, R2_i, meta

    spec_1 = load_reflectance_spec(csv_file_1, y_selector=FIT_Y_SELECTOR_0DEG)
    spec_2 = load_reflectance_spec(csv_file_2, y_selector=FIT_Y_SELECTOR_2DEG)
    validate_dual_fit_inputs(spec_1, THETA1, spec_2, THETA2)

    lam_nm, R1_i, R2_i = unify_two_reflectance_curves(
        spec_1.x_nm,
        spec_1.y,
        spec_2.x_nm,
        spec_2.y,
        wmin_nm=LAMBDA_MIN_NM,
        wmax_nm=LAMBDA_MAX_NM,
        n_lambda=N_LAMBDA,
    )
    meta = {
        "input_mode": "direct_csv",
        "curve_1_source": str(csv_file_1),
        "curve_2_source": str(csv_file_2),
    }
    return lam_nm, R1_i, R2_i, meta


def preview_csv(
    path: Path,
    y_selector: Optional[Union[int, str]] = None,
    save_plot: bool = True,
) -> SpectrumData:
    spec = load_spectrum_csv(path, y_selector=y_selector)

    print("=" * 90)
    print("CSV preview")
    print("=" * 90)
    print(f"path          = {spec.path}")
    print(f"all columns   = {spec.all_column_labels}")
    print(f"x_label       = {spec.x_label}")
    print(f"y_label       = {spec.y_label}")
    print(f"y_kind        = {spec.y_kind}")
    print(f"n_points      = {len(spec.x_nm)}")
    print(f"x range (nm)  = {spec.x_nm.min():.6f} ~ {spec.x_nm.max():.6f}")
    print(f"y range       = {spec.y.min():.6f} ~ {spec.y.max():.6f}")

    preview_df = pd.DataFrame(
        {
            "wavelength_nm": spec.x_nm,
            spec.y_label: spec.y,
        }
    )
    print("\nHead:")
    print(preview_df.head(10).to_string(index=False))

    plt.figure(figsize=(8, 5))
    plt.plot(spec.x_nm, spec.y, linewidth=1.8)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel(spec.y_label)
    plt.title(f"Preview: {spec.path.name}")
    plt.grid(True)
    plt.tight_layout()

    if save_plot:
        out_path = OUTPUT_DIR / f"{spec.path.stem}_preview.png"
        plt.savefig(out_path, dpi=200)
        print(f"Saved plot: {out_path}")

    plt.show()

    lines = [
        "CSV preview summary",
        f"path = {spec.path}",
        f"all_columns = {spec.all_column_labels}",
        f"x_label = {spec.x_label}",
        f"y_label = {spec.y_label}",
        f"y_kind = {spec.y_kind}",
        f"n_points = {len(spec.x_nm)}",
        f"x_range_nm = {spec.x_nm.min():.6f} ~ {spec.x_nm.max():.6f}",
        f"y_range = {spec.y.min():.6f} ~ {spec.y.max():.6f}",
    ]
    save_text_report(f"{spec.path.stem}_preview_summary.txt", lines)

    return spec


def export_clean_csv(
    input_path: Path,
    output_path: Path,
    y_selector: Optional[Union[int, str]] = None,
) -> SpectrumData:
    spec = load_spectrum_csv(input_path, y_selector=y_selector)

    df_out = pd.DataFrame(
        {
            "wavelength_nm": spec.x_nm,
            spec.y_label: spec.y,
        }
    )
    df_out.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Saved cleaned csv: {output_path}")

    payload = {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "all_columns": spec.all_column_labels,
        "x_label": spec.x_label,
        "y_label": spec.y_label,
        "y_kind": spec.y_kind,
        "n_points": int(len(spec.x_nm)),
    }
    save_json_report(f"{output_path.stem}_export_summary.json", payload)
    return spec


# =========================================================
# 7. 曲线插值/统一网格
# =========================================================
def interpolate_to_grid(w_nm: np.ndarray, y: np.ndarray, grid_nm: np.ndarray) -> np.ndarray:
    return np.interp(grid_nm, w_nm, y)


def unify_two_reflectance_curves(
    w1_nm: np.ndarray,
    R1: np.ndarray,
    w2_nm: np.ndarray,
    R2: np.ndarray,
    wmin_nm: float = 400.0,
    wmax_nm: float = 800.0,
    n_lambda: int = 300,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    w_min = max(np.min(w1_nm), np.min(w2_nm), wmin_nm)
    w_max = min(np.max(w1_nm), np.max(w2_nm), wmax_nm)

    if w_max <= w_min:
        raise ValueError("两条曲线没有共同波长区间。")

    grid_nm = np.linspace(w_min, w_max, n_lambda)
    R1_i = interpolate_to_grid(w1_nm, R1, grid_nm)
    R2_i = interpolate_to_grid(w2_nm, R2, grid_nm)
    return grid_nm, R1_i, R2_i


def evaluate_dispersion_profile(
    lam: np.ndarray,
    n_base: float,
    b_term: float,
    c_term: float,
) -> np.ndarray:
    lam = np.asarray(lam, dtype=float)
    if not USE_DISPERSION:
        return np.full_like(lam, float(n_base), dtype=float)

    form = str(DISPERSION_FORM).strip().lower()
    if form != "cauchy_um":
        raise ValueError(
            f"Unsupported DISPERSION_FORM '{DISPERSION_FORM}'. "
            "Currently only 'cauchy_um' is supported."
        )

    lam_um = lam * 1e6
    lam_um = np.clip(lam_um, 1e-9, None)
    return (
        float(n_base)
        + float(b_term) / (lam_um ** 2)
        + float(c_term) / (lam_um ** 4)
    )


# =========================================================
# 8. 光学模型：斜入射单层膜反射率
# =========================================================
def thinfilm_reflectance_angle(
    lam: np.ndarray,
    n0: float,
    n1: float,
    n2: float,
    d: float,
    theta0_deg: float,
    pol: str = "avg",
    mix_p_weight: float = 0.5,
) -> np.ndarray:
    lam = np.asarray(lam, dtype=float)
    theta0 = np.deg2rad(theta0_deg)
    n0_arr = np.full_like(lam, float(n0), dtype=float)
    n1_arr = evaluate_dispersion_profile(lam, n1, N1_DISPERSION_B, N1_DISPERSION_C)
    n2_arr = evaluate_dispersion_profile(lam, n2, N2_DISPERSION_B, N2_DISPERSION_C)

    sin_theta1 = n0_arr * np.sin(theta0) / n1_arr
    sin_theta2 = n0_arr * np.sin(theta0) / n2_arr

    sin_theta1 = np.clip(sin_theta1, -1.0, 1.0)
    sin_theta2 = np.clip(sin_theta2, -1.0, 1.0)

    theta1 = np.arcsin(sin_theta1)
    theta2 = np.arcsin(sin_theta2)

    c0 = np.cos(theta0)
    c1 = np.cos(theta1)
    c2 = np.cos(theta2)

    beta = 2 * np.pi * n1_arr * d * c1 / lam

    r01_s = (n0_arr * c0 - n1_arr * c1) / (n0_arr * c0 + n1_arr * c1)
    r12_s = (n1_arr * c1 - n2_arr * c2) / (n1_arr * c1 + n2_arr * c2)
    r_s = (r01_s + r12_s * np.exp(2j * beta)) / (1 + r01_s * r12_s * np.exp(2j * beta))
    R_s = np.abs(r_s) ** 2

    r01_p = (n1_arr * c0 - n0_arr * c1) / (n1_arr * c0 + n0_arr * c1)
    r12_p = (n2_arr * c1 - n1_arr * c2) / (n2_arr * c1 + n1_arr * c2)
    r_p = (r01_p + r12_p * np.exp(2j * beta)) / (1 + r01_p * r12_p * np.exp(2j * beta))
    R_p = np.abs(r_p) ** 2

    if pol == "s":
        return R_s
    if pol == "p":
        return R_p
    if pol == "avg":
        return 0.5 * (R_s + R_p)
    if pol == "mix":
        eta = float(np.clip(mix_p_weight, 0.0, 1.0))
        return eta * R_p + (1.0 - eta) * R_s
    raise ValueError("pol 必须是 's'、'p' 或 'avg'")


# =========================================================
# 9. baseline 拟合
# =========================================================
def fit_linear_baseline(
    residual: np.ndarray,
    x: np.ndarray,
    lambda_a: float = 1.0,
    lambda_b: float = 1.0,
) -> Tuple[float, float]:
    X = np.column_stack([np.ones_like(x), x])
    L = np.diag([lambda_a, lambda_b])
    beta = np.linalg.solve(X.T @ X + L, X.T @ residual)
    a_fit, b_fit = beta
    return float(a_fit), float(b_fit)


# =========================================================
# 10. 单角/双角反演
# =========================================================
def _safe_scale(value: float, eps: float = 1e-12) -> float:
    return max(float(value), eps)


def _ensure_odd_window(window: int) -> int:
    window = max(int(window), 1)
    if window % 2 == 0:
        window += 1
    return window


def smooth_signal_1d(y: np.ndarray, window: int = 1) -> np.ndarray:
    y = np.asarray(y, dtype=float).ravel()
    window = _ensure_odd_window(window)
    if window <= 1 or window >= len(y):
        return y.copy()

    pad = window // 2
    kernel = np.ones(window, dtype=float) / float(window)
    y_pad = np.pad(y, (pad, pad), mode="edge")
    return np.convolve(y_pad, kernel, mode="valid")


def standardize_signal(y: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    y = np.asarray(y, dtype=float).ravel()
    return (y - np.mean(y)) / _safe_scale(np.std(y), eps=eps)


def evaluate_curve_objective(
    lam: np.ndarray,
    y_obs: np.ndarray,
    y_model: np.ndarray,
    lambda_a: float,
    lambda_b: float,
    smooth_window: int,
    weight_level: float,
    weight_shape: float,
    weight_slope: float,
) -> Tuple[float, Tuple[float, float], Dict[str, float]]:
    lam = np.asarray(lam, dtype=float).ravel()
    y_obs = np.asarray(y_obs, dtype=float).ravel()
    y_model = np.asarray(y_model, dtype=float).ravel()

    lam_span = _safe_scale(np.max(lam) - np.min(lam), eps=1e-18)
    lam_norm = (lam - np.mean(lam)) / lam_span

    a_fit, b_fit = fit_linear_baseline(
        y_obs - y_model,
        lam_norm,
        lambda_a=lambda_a,
        lambda_b=lambda_b,
    )
    y_model_adj = y_model + a_fit + b_fit * lam_norm

    y_obs_s = smooth_signal_1d(y_obs, window=smooth_window)
    y_model_s = smooth_signal_1d(y_model_adj, window=smooth_window)

    level_err = float(
        np.mean((y_obs_s - y_model_s) ** 2) / _safe_scale(np.var(y_obs_s))
    )

    y_obs_shape = standardize_signal(y_obs_s)
    y_model_shape = standardize_signal(y_model_s)
    shape_err = float(np.mean((y_obs_shape - y_model_shape) ** 2))

    slope_obs = standardize_signal(np.gradient(y_obs_s, lam_norm))
    slope_model = standardize_signal(np.gradient(y_model_s, lam_norm))
    slope_err = float(np.mean((slope_obs - slope_model) ** 2))

    total_err = float(
        weight_level * level_err
        + weight_shape * shape_err
        + weight_slope * slope_err
    )

    metrics = {
        "level_err": level_err,
        "shape_err": shape_err,
        "slope_err": slope_err,
        "a_fit": float(a_fit),
        "b_fit": float(b_fit),
    }
    return total_err, (float(a_fit), float(b_fit)), metrics


def evaluate_dual_fit_objective(
    lam: np.ndarray,
    R1: np.ndarray,
    theta1: float,
    R2: np.ndarray,
    theta2: float,
    d: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str,
    mix_p_weight: float,
    lambda_a: float,
    lambda_b: float,
    smooth_window: int,
    weight_level: float,
    weight_shape: float,
    weight_slope: float,
) -> Tuple[float, Tuple[float, float, float, float], Dict[str, Dict[str, float]]]:
    Rm1 = thinfilm_reflectance_angle(lam, n0, n1, n2, d, theta1, pol=pol, mix_p_weight=mix_p_weight)
    Rm2 = thinfilm_reflectance_angle(lam, n0, n1, n2, d, theta2, pol=pol, mix_p_weight=mix_p_weight)
    lam_span = _safe_scale(np.max(lam) - np.min(lam), eps=1e-18)
    lam_norm = (lam - np.mean(lam)) / lam_span

    err1, (a1, b1), metrics1 = evaluate_curve_objective(
        lam=lam,
        y_obs=R1,
        y_model=Rm1,
        lambda_a=lambda_a,
        lambda_b=lambda_b,
        smooth_window=smooth_window,
        weight_level=weight_level,
        weight_shape=weight_shape,
        weight_slope=weight_slope,
    )
    err2, (a2, b2), metrics2 = evaluate_curve_objective(
        lam=lam,
        y_obs=R2,
        y_model=Rm2,
        lambda_a=lambda_a,
        lambda_b=lambda_b,
        smooth_window=smooth_window,
        weight_level=weight_level,
        weight_shape=weight_shape,
        weight_slope=weight_slope,
    )

    Rm1_adj = Rm1 + a1 + b1 * lam_norm
    Rm2_adj = Rm2 + a2 + b2 * lam_norm

    delta_obs = smooth_signal_1d(R2 - R1, window=smooth_window)
    delta_model = smooth_signal_1d(Rm2_adj - Rm1_adj, window=smooth_window)
    delta_shape_err = float(
        np.mean((standardize_signal(delta_obs) - standardize_signal(delta_model)) ** 2)
    )
    delta_slope_err = float(
        np.mean(
            (
                standardize_signal(np.gradient(delta_obs, lam_norm))
                - standardize_signal(np.gradient(delta_model, lam_norm))
            ) ** 2
        )
    )

    common_err = float(0.5 * (err1 + err2))
    delta_err = float(0.35 * delta_shape_err + 0.65 * delta_slope_err)
    total_err = float(0.55 * common_err + 0.45 * delta_err)
    baseline_params = (float(a1), float(b1), float(a2), float(b2))
    metrics = {
        "curve_1": metrics1,
        "curve_2": metrics2,
        "cross_angle": {
            "delta_shape_err": delta_shape_err,
            "delta_slope_err": delta_slope_err,
            "common_err": common_err,
            "delta_err": delta_err,
        },
    }
    return total_err, baseline_params, metrics


def pick_distinct_search_seeds(
    heatmap: np.ndarray,
    d_grid_nm: np.ndarray,
    theta_grid_deg: np.ndarray,
    top_k: int,
    min_d_separation_nm: float,
    min_theta_separation_deg: float,
) -> List[Dict[str, float]]:
    seeds: List[Dict[str, float]] = []
    flat_order = np.argsort(heatmap, axis=None)

    for flat_idx in flat_order:
        i, j = np.unravel_index(flat_idx, heatmap.shape)
        cand = {
            "d_nm": float(d_grid_nm[j]),
            "theta2_deg": float(theta_grid_deg[i]),
            "objective": float(heatmap[i, j]),
        }

        is_far_enough = True
        for seed in seeds:
            if (
                abs(cand["d_nm"] - seed["d_nm"]) < min_d_separation_nm
                and abs(cand["theta2_deg"] - seed["theta2_deg"]) < min_theta_separation_deg
            ):
                is_far_enough = False
                break

        if is_far_enough:
            seeds.append(cand)
            if len(seeds) >= top_k:
                break

    return seeds


def multiscale_dual_search(
    lam: np.ndarray,
    R1: np.ndarray,
    theta1_fixed: float,
    R2: np.ndarray,
    theta2_nominal: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str,
    mix_p_weight: float,
    d_min: float,
    d_max: float,
    lambda_a: float,
    lambda_b: float,
    theta2_min: float,
    theta2_max: float,
    smooth_window: int = OBJECTIVE_SMOOTH_WINDOW,
    weight_level: float = OBJECTIVE_WEIGHT_LEVEL,
    weight_shape: float = OBJECTIVE_WEIGHT_SHAPE,
    weight_slope: float = OBJECTIVE_WEIGHT_SLOPE,
    coarse_d_step_nm: float = SEARCH_COARSE_D_STEP_NM,
    coarse_theta_step_deg: float = SEARCH_COARSE_THETA_STEP_DEG,
    top_k: int = SEARCH_TOP_K,
    min_d_separation_nm: float = SEARCH_MIN_D_SEPARATION_NM,
    min_theta_separation_deg: float = SEARCH_MIN_THETA_SEPARATION_DEG,
) -> Dict:
    d_min_nm = float(d_min * 1e9)
    d_max_nm = float(d_max * 1e9)

    d_grid_nm = np.arange(d_min_nm, d_max_nm + 1e-12, coarse_d_step_nm)
    theta_grid_deg = np.arange(theta2_min, theta2_max + 1e-12, coarse_theta_step_deg)
    if len(theta_grid_deg) == 0:
        theta_grid_deg = np.array([theta2_nominal], dtype=float)

    def objective_from_nm_deg(d_nm: float, theta2_deg: float):
        return evaluate_dual_fit_objective(
            lam=lam,
            R1=R1,
            theta1=theta1_fixed,
            R2=R2,
            theta2=theta2_deg,
            d=d_nm * 1e-9,
            n0=n0,
            n1=n1,
            n2=n2,
            pol=pol,
            mix_p_weight=mix_p_weight,
            lambda_a=lambda_a,
            lambda_b=lambda_b,
            smooth_window=smooth_window,
            weight_level=weight_level,
            weight_shape=weight_shape,
            weight_slope=weight_slope,
        )

    def optimize_d_for_fixed_theta(
        theta2_deg: float,
        d_left_nm: float,
        d_right_nm: float,
        d_step_nm: float,
    ) -> Dict[str, float]:
        local_d_grid_nm = np.arange(d_left_nm, d_right_nm + 1e-12, d_step_nm)
        if len(local_d_grid_nm) == 0:
            local_d_grid_nm = np.array([d_left_nm], dtype=float)

        err_grid = np.zeros(len(local_d_grid_nm), dtype=float)
        best_idx = 0
        best_pack = None
        for idx, d_nm in enumerate(local_d_grid_nm):
            err, baseline_params, metrics = objective_from_nm_deg(float(d_nm), float(theta2_deg))
            err_grid[idx] = err
            if best_pack is None or err < best_pack["objective"]:
                best_idx = idx
                best_pack = {
                    "d_nm": float(d_nm),
                    "theta2_deg": float(theta2_deg),
                    "objective": float(err),
                    "baseline_params": baseline_params,
                    "metrics": metrics,
                }

        center_nm = float(local_d_grid_nm[best_idx])
        refine_half_window_nm = max(4.0 * d_step_nm, 6.0)
        left_nm = max(d_left_nm, center_nm - refine_half_window_nm)
        right_nm = min(d_right_nm, center_nm + refine_half_window_nm)

        if right_nm > left_nm:
            res_d = minimize_scalar(
                lambda d_nm: objective_from_nm_deg(float(d_nm), float(theta2_deg))[0],
                bounds=(left_nm, right_nm),
                method="bounded",
                options={"xatol": 1e-3},
            )
            err_try, baseline_try, metrics_try = objective_from_nm_deg(float(res_d.x), float(theta2_deg))
            if err_try < best_pack["objective"]:
                best_pack = {
                    "d_nm": float(res_d.x),
                    "theta2_deg": float(theta2_deg),
                    "objective": float(err_try),
                    "baseline_params": baseline_try,
                    "metrics": metrics_try,
                }

        return best_pack

    heatmap = np.zeros((len(theta_grid_deg), len(d_grid_nm)), dtype=float)
    theta_candidates = []
    for i, theta2_test in enumerate(theta_grid_deg):
        row_best = None
        for j, d_nm in enumerate(d_grid_nm):
            err, _, _ = objective_from_nm_deg(float(d_nm), float(theta2_test))
            heatmap[i, j] = err
            if row_best is None or err < row_best["objective"]:
                row_best = {
                    "d_nm": float(d_nm),
                    "theta2_deg": float(theta2_test),
                    "objective": float(err),
                }

        theta_candidates.append(
            optimize_d_for_fixed_theta(
                theta2_deg=float(theta2_test),
                d_left_nm=d_min_nm,
                d_right_nm=d_max_nm,
                d_step_nm=coarse_d_step_nm,
            )
        )

    theta_candidates = sorted(theta_candidates, key=lambda x: x["objective"])
    seeds = []
    for cand in theta_candidates:
        is_far_enough = True
        for seed in seeds:
            if (
                abs(cand["d_nm"] - seed["d_nm"]) < min_d_separation_nm
                and abs(cand["theta2_deg"] - seed["theta2_deg"]) < min_theta_separation_deg
            ):
                is_far_enough = False
                break

        if is_far_enough:
            seeds.append({
                "d_nm": float(cand["d_nm"]),
                "theta2_deg": float(cand["theta2_deg"]),
                "objective": float(cand["objective"]),
            })
            if len(seeds) >= top_k:
                break

    if len(seeds) == 0:
        raise ValueError("Multiscale search failed to find a valid seed.")

    best_solution = None
    search_trace = []

    for seed in seeds:
        d_best_nm = float(seed["d_nm"])
        theta_best = float(seed["theta2_deg"])
        best_err, baseline_params, metrics = objective_from_nm_deg(d_best_nm, theta_best)
        stage_trace = [{
            "stage": "seed",
            "d_nm": d_best_nm,
            "theta2_deg": theta_best,
            "objective": float(best_err),
        }]

        for d_window_nm, theta_window_deg in zip(REFINE_D_WINDOWS_NM, REFINE_THETA_WINDOWS_DEG):
            d_left = max(d_min_nm, d_best_nm - d_window_nm)
            d_right = min(d_max_nm, d_best_nm + d_window_nm)
            theta_left = max(theta2_min, theta_best - theta_window_deg)
            theta_right = min(theta2_max, theta_best + theta_window_deg)

            if theta_right > theta_left:
                theta_step = max(theta_window_deg / 8.0, 0.01)
                local_theta_grid = np.arange(theta_left, theta_right + 1e-12, theta_step)
            else:
                local_theta_grid = np.array([theta_best], dtype=float)

            local_best = None
            local_d_step_nm = max(d_window_nm / 18.0, 0.08)
            for theta2_test in local_theta_grid:
                cand = optimize_d_for_fixed_theta(
                    theta2_deg=float(theta2_test),
                    d_left_nm=d_left,
                    d_right_nm=d_right,
                    d_step_nm=local_d_step_nm,
                )
                if local_best is None or cand["objective"] < local_best["objective"]:
                    local_best = cand

            d_best_nm = float(local_best["d_nm"])
            theta_best = float(local_best["theta2_deg"])
            best_err = float(local_best["objective"])
            baseline_params = local_best["baseline_params"]
            metrics = local_best["metrics"]

            if theta_right > theta_left:
                res_theta = minimize_scalar(
                    lambda theta_deg: optimize_d_for_fixed_theta(
                        theta2_deg=float(theta_deg),
                        d_left_nm=d_left,
                        d_right_nm=d_right,
                        d_step_nm=max(local_d_step_nm / 2.0, 0.05),
                    )["objective"],
                    bounds=(theta_left, theta_right),
                    method="bounded",
                    options={"xatol": 1e-4},
                )
                cand = optimize_d_for_fixed_theta(
                    theta2_deg=float(res_theta.x),
                    d_left_nm=d_left,
                    d_right_nm=d_right,
                    d_step_nm=max(local_d_step_nm / 2.0, 0.05),
                )
                if cand["objective"] < best_err:
                    d_best_nm = float(cand["d_nm"])
                    theta_best = float(cand["theta2_deg"])
                    best_err = float(cand["objective"])
                    baseline_params = cand["baseline_params"]
                    metrics = cand["metrics"]

            stage_trace.append({
                "stage": f"window_d_{d_window_nm:.3f}_theta_{theta_window_deg:.3f}",
                "d_nm": float(d_best_nm),
                "theta2_deg": float(theta_best),
                "objective": float(best_err),
            })

        candidate = {
            "d_fit_m": float(d_best_nm * 1e-9),
            "d_fit_nm": float(d_best_nm),
            "theta2_fit_deg": float(theta_best),
            "best_objective": float(best_err),
            "baseline_params": tuple(float(x) for x in baseline_params),
            "metrics": metrics,
            "stage_trace": stage_trace,
        }
        search_trace.append(candidate)

        if best_solution is None or candidate["best_objective"] < best_solution["best_objective"]:
            best_solution = candidate

    best_solution["coarse_heatmap"] = heatmap
    best_solution["coarse_d_grid_nm"] = d_grid_nm
    best_solution["coarse_theta2_grid_deg"] = theta_grid_deg
    best_solution["coarse_seeds"] = seeds
    best_solution["all_candidates"] = search_trace
    return best_solution


def invert_thickness_single_only(
    lam: np.ndarray,
    R_target: np.ndarray,
    n0: float,
    n1: float,
    n2: float,
    theta_deg: float,
    pol: str = "avg",
    d_min: float = 20e-9,
    d_max: float = 300e-9,
    n_grid: int = 1500,
) -> float:
    def objective(d: float) -> float:
        R_model = thinfilm_reflectance_angle(lam, n0, n1, n2, d, theta_deg, pol=pol)
        return float(np.mean((R_model - R_target) ** 2))

    d_grid = np.linspace(d_min, d_max, n_grid)
    err_grid = np.array([objective(d) for d in d_grid])
    d0 = float(d_grid[np.argmin(err_grid)])

    left = max(d_min, d0 - 20e-9)
    right = min(d_max, d0 + 20e-9)

    result = minimize_scalar(
        objective,
        bounds=(left, right),
        method="bounded",
        options={"xatol": 1e-12},
    )
    return float(result.x)


def invert_thickness_single_detrend(
    lam: np.ndarray,
    R_target: np.ndarray,
    n0: float,
    n1: float,
    n2: float,
    theta_deg: float,
    pol: str = "avg",
    d_min: float = 20e-9,
    d_max: float = 300e-9,
    lambda_a: float = 1.0,
    lambda_b: float = 1.0,
    n_iter: int = 2,
    n_grid: int = 1500,
) -> Tuple[float, float, float, np.ndarray]:
    lam_norm = (lam - lam.mean()) / (lam.max() - lam.min())
    R_work = R_target.copy()

    a_total = 0.0
    b_total = 0.0
    d_fit = None

    for _ in range(n_iter):
        d_fit = invert_thickness_single_only(
            lam, R_work, n0, n1, n2, theta_deg, pol=pol,
            d_min=d_min, d_max=d_max, n_grid=n_grid
        )

        R_model = thinfilm_reflectance_angle(lam, n0, n1, n2, d_fit, theta_deg, pol=pol)
        residual = R_work - R_model

        a_fit, b_fit = fit_linear_baseline(
            residual, lam_norm, lambda_a=lambda_a, lambda_b=lambda_b
        )

        R_work = R_work - (a_fit + b_fit * lam_norm)
        a_total += a_fit
        b_total += b_fit

    return float(d_fit), float(a_total), float(b_total), R_work


def invert_thickness_dual_only(
    lam: np.ndarray,
    R1: np.ndarray,
    theta1: float,
    R2: np.ndarray,
    theta2: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str = "avg",
    d_min: float = 20e-9,
    d_max: float = 300e-9,
    n_grid: int = 1500,
) -> float:
    def objective(d: float) -> float:
        Rm1 = thinfilm_reflectance_angle(lam, n0, n1, n2, d, theta1, pol=pol)
        Rm2 = thinfilm_reflectance_angle(lam, n0, n1, n2, d, theta2, pol=pol)
        e1 = np.mean((Rm1 - R1) ** 2)
        e2 = np.mean((Rm2 - R2) ** 2)
        return float(0.5 * (e1 + e2))

    d_grid = np.linspace(d_min, d_max, n_grid)
    err_grid = np.array([objective(d) for d in d_grid])
    d0 = float(d_grid[np.argmin(err_grid)])

    left = max(d_min, d0 - 20e-9)
    right = min(d_max, d0 + 20e-9)

    result = minimize_scalar(
        objective,
        bounds=(left, right),
        method="bounded",
        options={"xatol": 1e-12},
    )
    return float(result.x)


def invert_thickness_dual_detrend(
    lam: np.ndarray,
    R1: np.ndarray,
    theta1: float,
    R2: np.ndarray,
    theta2: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str = "avg",
    d_min: float = 20e-9,
    d_max: float = 300e-9,
    lambda_a: float = 1.0,
    lambda_b: float = 1.0,
    n_iter: int = 2,
    n_grid: int = 1500,
) -> Tuple[float, np.ndarray, np.ndarray, Tuple[float, float, float, float]]:
    lam_norm = (lam - lam.mean()) / (lam.max() - lam.min())
    R1_work = R1.copy()
    R2_work = R2.copy()

    a1_total = 0.0
    b1_total = 0.0
    a2_total = 0.0
    b2_total = 0.0

    d_fit = None

    for _ in range(n_iter):
        d_fit = invert_thickness_dual_only(
            lam, R1_work, theta1, R2_work, theta2, n0, n1, n2,
            pol=pol, d_min=d_min, d_max=d_max, n_grid=n_grid
        )

        Rm1 = thinfilm_reflectance_angle(lam, n0, n1, n2, d_fit, theta1, pol=pol)
        Rm2 = thinfilm_reflectance_angle(lam, n0, n1, n2, d_fit, theta2, pol=pol)

        res1 = R1_work - Rm1
        res2 = R2_work - Rm2

        a1, b1 = fit_linear_baseline(res1, lam_norm, lambda_a=lambda_a, lambda_b=lambda_b)
        a2, b2 = fit_linear_baseline(res2, lam_norm, lambda_a=lambda_a, lambda_b=lambda_b)

        R1_work = R1_work - (a1 + b1 * lam_norm)
        R2_work = R2_work - (a2 + b2 * lam_norm)

        a1_total += a1
        b1_total += b1
        a2_total += a2
        b2_total += b2

    baseline_params = (float(a1_total), float(b1_total), float(a2_total), float(b2_total))
    return float(d_fit), R1_work, R2_work, baseline_params


def invert_thickness_dual_with_theta2_search(
    lam: np.ndarray,
    R1: np.ndarray,
    theta1_nominal: float,
    R2: np.ndarray,
    theta2_nominal: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str = "avg",
    d_min: float = 20e-9,
    d_max: float = 300e-9,
    lambda_a: float = 1.0,
    lambda_b: float = 1.0,
    n_iter: int = 2,
    n_grid: int = 1500,
    theta2_search_min: float = -3.0,
    theta2_search_max: float = 3.0,
    theta2_search_step: float = 0.25,
) -> Tuple[float, float, float, Tuple[float, float, float, float]]:
    theta2_candidates = np.arange(
        theta2_nominal + theta2_search_min,
        theta2_nominal + theta2_search_max + 1e-12,
        theta2_search_step,
    )

    best_err = np.inf
    d_fit_best = None
    theta2_best = None
    baseline_params_best = None

    for theta2_test in theta2_candidates:
        d_fit, R1_corr, R2_corr, baseline_params = invert_thickness_dual_detrend(
            lam, R1, theta1_nominal, R2, theta2_test, n0, n1, n2,
            pol=pol,
            d_min=d_min, d_max=d_max,
            lambda_a=lambda_a, lambda_b=lambda_b,
            n_iter=n_iter, n_grid=n_grid
        )

        Rm1 = thinfilm_reflectance_angle(lam, n0, n1, n2, d_fit, theta1_nominal, pol=pol)
        Rm2 = thinfilm_reflectance_angle(lam, n0, n1, n2, d_fit, theta2_test, pol=pol)

        err1 = np.mean((Rm1 - R1_corr) ** 2)
        err2 = np.mean((Rm2 - R2_corr) ** 2)
        total_err = float(0.5 * (err1 + err2))

        if total_err < best_err:
            best_err = total_err
            d_fit_best = d_fit
            theta2_best = float(theta2_test)
            baseline_params_best = baseline_params

    return float(d_fit_best), float(theta2_best), float(best_err), baseline_params_best


# =========================================================
# 11. 绘图
# =========================================================
def plot_dual_fit(
    lam_nm: np.ndarray,
    R1_raw: np.ndarray,
    R2_raw: np.ndarray,
    d_fit: float,
    baseline_params: Tuple[float, float, float, float],
    theta1_used: float,
    theta2_used: float,
    mix_p_weight: float = 0.5,
    out_prefix: str = "fit",
) -> None:
    a1, b1, a2, b2 = baseline_params
    lam = lam_nm * 1e-9
    lam_norm = (lam - lam.mean()) / (lam.max() - lam.min())

    Rm1 = thinfilm_reflectance_angle(lam, N0, N1, N2, d_fit, theta1_used, pol=POL, mix_p_weight=mix_p_weight)
    Rm2 = thinfilm_reflectance_angle(lam, N0, N1, N2, d_fit, theta2_used, pol=POL, mix_p_weight=mix_p_weight)

    baseline1 = a1 + b1 * lam_norm
    baseline2 = a2 + b2 * lam_norm

    Rfit1 = Rm1 + baseline1
    Rfit2 = Rm2 + baseline2

    plt.figure(figsize=(8, 5))
    plt.plot(lam_nm, R1_raw, label=f"Exp {theta1_used:.1f}°", linewidth=1.5)
    plt.plot(lam_nm, Rfit1, "--", label=f"Fit {theta1_used:.1f}°", linewidth=2)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"Dual-angle fit at {theta1_used:.1f}°")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_{str(theta1_used).replace('.', '_')}deg.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(lam_nm, R2_raw, label=f"Exp {theta2_used:.1f}°", linewidth=1.5)
    plt.plot(lam_nm, Rfit2, "--", label=f"Fit {theta2_used:.1f}°", linewidth=2)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"Dual-angle fit at {theta2_used:.1f}°")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_{str(theta2_used).replace('.', '_')}deg.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(lam_nm, R1_raw - Rfit1, label=f"Residual {theta1_used:.1f}°")
    plt.plot(lam_nm, R2_raw - Rfit2, label=f"Residual {theta2_used:.1f}°")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Residual")
    plt.title("Dual-angle residuals")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_residuals.png", dpi=200)
    plt.show()


# =========================================================
# 12. 单样品拟合
# =========================================================
def run_dual_theta2_search_once(
    lam: np.ndarray,
    R1_i: np.ndarray,
    R2_i: np.ndarray,
    mix_p_weight: float,
) -> Tuple[Dict, Dict]:
    nominal_search = multiscale_dual_search(
        lam=lam,
        R1=R1_i,
        theta1_fixed=THETA1,
        R2=R2_i,
        theta2_nominal=THETA2,
        n0=N0,
        n1=N1,
        n2=N2,
        pol=POL,
        mix_p_weight=mix_p_weight,
        d_min=D_MIN,
        d_max=D_MAX,
        lambda_a=LAMBDA_A,
        lambda_b=LAMBDA_B,
        theta2_min=THETA2,
        theta2_max=THETA2,
    )
    corrected_search = multiscale_dual_search(
        lam=lam,
        R1=R1_i,
        theta1_fixed=THETA1,
        R2=R2_i,
        theta2_nominal=THETA2,
        n0=N0,
        n1=N1,
        n2=N2,
        pol=POL,
        mix_p_weight=mix_p_weight,
        d_min=D_MIN,
        d_max=D_MAX,
        lambda_a=LAMBDA_A,
        lambda_b=LAMBDA_B,
        theta2_min=THETA2 + THETA2_SEARCH_MIN,
        theta2_max=THETA2 + THETA2_SEARCH_MAX,
    )
    return nominal_search, corrected_search


def fit_mix_weight_from_dual_csv(
    lam: np.ndarray,
    R1_i: np.ndarray,
    R2_i: np.ndarray,
) -> Tuple[float, Dict, Dict]:
    weight_candidates = np.arange(
        MIX_WEIGHT_SEARCH_MIN,
        MIX_WEIGHT_SEARCH_MAX + 1e-12,
        MIX_WEIGHT_SEARCH_STEP,
    )
    if len(weight_candidates) == 0:
        weight_candidates = np.array([MIX_P_WEIGHT], dtype=float)

    best_pack = None
    for eta in weight_candidates:
        nominal_search, corrected_search = run_dual_theta2_search_once(
            lam=lam,
            R1_i=R1_i,
            R2_i=R2_i,
            mix_p_weight=float(eta),
        )
        objective = float(corrected_search["best_objective"])
        if best_pack is None or objective < best_pack["objective"]:
            best_pack = {
                "mix_p_weight": float(eta),
                "objective": objective,
                "nominal_search": nominal_search,
                "corrected_search": corrected_search,
            }

    left = max(MIX_WEIGHT_SEARCH_MIN, best_pack["mix_p_weight"] - max(MIX_WEIGHT_SEARCH_STEP, 0.05))
    right = min(MIX_WEIGHT_SEARCH_MAX, best_pack["mix_p_weight"] + max(MIX_WEIGHT_SEARCH_STEP, 0.05))
    if right > left:
        res = minimize_scalar(
            lambda eta: run_dual_theta2_search_once(
                lam=lam,
                R1_i=R1_i,
                R2_i=R2_i,
                mix_p_weight=float(eta),
            )[1]["best_objective"],
            bounds=(left, right),
            method="bounded",
            options={"xatol": 1e-3},
        )
        nominal_search, corrected_search = run_dual_theta2_search_once(
            lam=lam,
            R1_i=R1_i,
            R2_i=R2_i,
            mix_p_weight=float(res.x),
        )
        if float(corrected_search["best_objective"]) < best_pack["objective"]:
            best_pack = {
                "mix_p_weight": float(res.x),
                "objective": float(corrected_search["best_objective"]),
                "nominal_search": nominal_search,
                "corrected_search": corrected_search,
            }

    return (
        float(best_pack["mix_p_weight"]),
        best_pack["nominal_search"],
        best_pack["corrected_search"],
    )


def fit_dual_csv_from_files(
    csv_file_1: Path,
    csv_file_2: Path,
    sample_id: str = "sample",
    save_plots: bool = True,
) -> Dict:
    sync_angle_config_aliases()
    lam_nm, R1_i, R2_i, input_meta = resolve_dual_fit_curves(csv_file_1, csv_file_2)
    lam = lam_nm * 1e-9

    nominal_search = multiscale_dual_search(
        lam=lam,
        R1=R1_i,
        theta1_fixed=THETA1,
        R2=R2_i,
        theta2_nominal=THETA2,
        n0=N0,
        n1=N1,
        n2=N2,
        pol=POL,
        mix_p_weight=MIX_P_WEIGHT,
        d_min=D_MIN,
        d_max=D_MAX,
        lambda_a=LAMBDA_A,
        lambda_b=LAMBDA_B,
        theta2_min=THETA2,
        theta2_max=THETA2,
    )

    d_fit = float(nominal_search["d_fit_m"])
    d_fit_nm = float(nominal_search["d_fit_nm"])
    baseline_params = nominal_search["baseline_params"]
    d_fit_cal_nm = float(
        calibrate_thickness_nm(
            d_fit_nm,
            use_calibration=USE_THICKNESS_CALIBRATION,
            a=CAL_A,
            b=CAL_B,
        )
    )

    if save_plots:
        plot_dual_fit(
            lam_nm, R1_i, R2_i, d_fit, baseline_params,
            THETA1, THETA2, mix_p_weight=MIX_P_WEIGHT, out_prefix=f"{sample_id}_fit"
        )

    result = {
        "sample_id": sample_id,
        "csv_file_1": str(csv_file_1),
        "csv_file_2": str(csv_file_2),
        "theta1_fixed_deg": THETA1,
        "theta2_fixed_deg": THETA2,
        "d_fit_nm": d_fit_nm,
        "d_fit_calibrated_nm": d_fit_cal_nm,
        "search_method": SEARCH_METHOD,
        "best_objective": float(nominal_search["best_objective"]),
        "input_mode": str(input_meta["input_mode"]),
        "curve_1_source": str(input_meta["curve_1_source"]),
        "curve_2_source": str(input_meta["curve_2_source"]),
        "use_dispersion": bool(USE_DISPERSION),
        "dispersion_form": str(DISPERSION_FORM),
        "n1_dispersion_b": float(N1_DISPERSION_B),
        "n1_dispersion_c": float(N1_DISPERSION_C),
        "n2_dispersion_b": float(N2_DISPERSION_B),
        "n2_dispersion_c": float(N2_DISPERSION_C),
    }
    if "mix_source_p_weight" in input_meta:
        result["mix_source_p_weight"] = float(input_meta["mix_source_p_weight"])
        result["mix_source_0deg_mode"] = str(input_meta["mix_source_0deg_mode"])
        result["mix_source_2deg_mode"] = str(input_meta["mix_source_2deg_mode"])
    return result


def fit_dual_csv_with_theta2_search_from_files(
    csv_file_1: Path,
    csv_file_2: Path,
    sample_id: str = "sample",
    save_plots: bool = True,
) -> Dict:
    sync_angle_config_aliases()
    lam_nm, R1_i, R2_i, input_meta = resolve_dual_fit_curves(csv_file_1, csv_file_2)
    lam = lam_nm * 1e-9

    mix_p_weight_fit = float(MIX_P_WEIGHT)
    if POL == "mix" and FIT_MIX_WEIGHT:
        mix_p_weight_fit, nominal_search, corrected_search = fit_mix_weight_from_dual_csv(
            lam=lam,
            R1_i=R1_i,
            R2_i=R2_i,
        )
    else:
        nominal_search, corrected_search = run_dual_theta2_search_once(
            lam=lam,
            R1_i=R1_i,
            R2_i=R2_i,
            mix_p_weight=mix_p_weight_fit,
        )

    d_nominal = float(nominal_search["d_fit_m"])
    d_fit = float(corrected_search["d_fit_m"])
    theta2_fit = float(corrected_search["theta2_fit_deg"])
    baseline_params_nominal = nominal_search["baseline_params"]
    baseline_params_best = corrected_search["baseline_params"]
    best_err = float(corrected_search["best_objective"])

    d_nominal_nm = float(nominal_search["d_fit_nm"])
    d_corrected_nm = float(corrected_search["d_fit_nm"])
    delta_d_nm = float(d_corrected_nm - d_nominal_nm)

    d_nominal_cal_nm = float(
        calibrate_thickness_nm(
            d_nominal_nm,
            use_calibration=USE_THICKNESS_CALIBRATION,
            a=CAL_A,
            b=CAL_B,
        )
    )
    d_corrected_cal_nm = float(
        calibrate_thickness_nm(
            d_corrected_nm,
            use_calibration=USE_THICKNESS_CALIBRATION,
            a=CAL_A,
            b=CAL_B,
        )
    )

    if save_plots:
        plot_dual_fit(
            lam_nm, R1_i, R2_i, d_nominal, baseline_params_nominal,
            THETA1, THETA2, mix_p_weight=mix_p_weight_fit, out_prefix=f"{sample_id}_nominal"
        )
        plot_dual_fit(
            lam_nm, R1_i, R2_i, d_fit, baseline_params_best,
            THETA1, theta2_fit, mix_p_weight=mix_p_weight_fit, out_prefix=f"{sample_id}_corrected"
        )

    result = {
        "sample_id": sample_id,
        "csv_file_1": str(csv_file_1),
        "csv_file_2": str(csv_file_2),
        "theta1_fixed_deg": THETA1,
        "theta2_nominal_deg": THETA2,
        "theta2_fit_deg": float(theta2_fit),
        "d_fit_nominal_nm": d_nominal_nm,
        "d_fit_corrected_nm": d_corrected_nm,
        "d_fit_nominal_calibrated_nm": d_nominal_cal_nm,
        "d_fit_corrected_calibrated_nm": d_corrected_cal_nm,
        "delta_d_nm": delta_d_nm,
        "best_objective": float(best_err),
        "nominal_objective": float(nominal_search["best_objective"]),
        "search_method": SEARCH_METHOD,
        "mix_p_weight_fit": mix_p_weight_fit,
        "input_mode": str(input_meta["input_mode"]),
        "curve_1_source": str(input_meta["curve_1_source"]),
        "curve_2_source": str(input_meta["curve_2_source"]),
        "use_dispersion": bool(USE_DISPERSION),
        "dispersion_form": str(DISPERSION_FORM),
        "n1_dispersion_b": float(N1_DISPERSION_B),
        "n1_dispersion_c": float(N1_DISPERSION_C),
        "n2_dispersion_b": float(N2_DISPERSION_B),
        "n2_dispersion_c": float(N2_DISPERSION_C),
        "nominal_search_trace": nominal_search["stage_trace"],
        "corrected_search_trace": corrected_search["stage_trace"],
        "coarse_seeds": corrected_search["coarse_seeds"],
    }
    if "mix_source_p_weight" in input_meta:
        result["mix_source_p_weight"] = float(input_meta["mix_source_p_weight"])
        result["mix_source_0deg_mode"] = str(input_meta["mix_source_0deg_mode"])
        result["mix_source_2deg_mode"] = str(input_meta["mix_source_2deg_mode"])
    return result


# =========================================================
# 12B. 诊断模块：0deg 单角扫描 + d-theta2 热图
# =========================================================
SCAN_D_MIN_NM = 5.0
SCAN_D_MAX_NM = 200.0
SCAN_D_STEP_NM = 0.2

HEATMAP_D_MIN_NM = 5.0
HEATMAP_D_MAX_NM = 200.0
HEATMAP_D_STEP_NM = 1.0

HEATMAP_THETA2_MIN_DEG = 70.0
HEATMAP_THETA2_MAX_DEG = 90.0
HEATMAP_THETA2_STEP_DEG = 0.25


def compute_single_angle_objective_curve(
    lam: np.ndarray,
    R_target: np.ndarray,
    theta_deg: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str,
    d_grid_nm: np.ndarray,
) -> np.ndarray:
    obj = []

    for d_nm in d_grid_nm:
        d = d_nm * 1e-9
        R_model = thinfilm_reflectance_angle(lam, n0, n1, n2, d, theta_deg, pol=pol)
        err = np.mean((R_model - R_target) ** 2)
        obj.append(float(err))

    return np.array(obj, dtype=float)


def plot_single_angle_scan_0deg(
    lam_nm: np.ndarray,
    R0_raw: np.ndarray,
    d_grid_nm: np.ndarray,
    obj_curve: np.ndarray,
    best_d_nm: float,
    out_prefix: str = "single_angle_0deg_scan",
) -> None:
    angle_label = format_angle_label(THETA1)
    plt.figure(figsize=(8, 5))
    plt.plot(d_grid_nm, obj_curve, linewidth=1.8)
    plt.axvline(best_d_nm, linestyle="--", label=f"best d = {best_d_nm:.3f} nm")
    plt.xlabel("Thickness (nm)")
    plt.ylabel("Objective (MSE)")
    plt.title(f"{angle_label} single-angle objective scan")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_objective.png", dpi=200)
    plt.show()

    lam = lam_nm * 1e-9
    R_best = thinfilm_reflectance_angle(
        lam, N0, N1, N2, best_d_nm * 1e-9, THETA1, pol=POL
    )

    plt.figure(figsize=(8, 5))
    plt.plot(lam_nm, R0_raw, label=f"COMSOL {angle_label}", linewidth=1.5)
    plt.plot(lam_nm, R_best, "--", label=f"Model best d={best_d_nm:.3f} nm", linewidth=2)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"{angle_label} single-angle fit check")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_fit.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(lam_nm, R0_raw - R_best, linewidth=1.5)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Residual")
    plt.title(f"{angle_label} single-angle residual")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_residual.png", dpi=200)
    plt.show()


def run_single_angle_0deg_scan() -> None:
    sync_angle_config_aliases()
    angle_label = format_angle_label(THETA1)
    w0_nm, R0 = read_reflectance_csv(CSV_FILE_0DEG, y_selector=FIT_Y_SELECTOR_0DEG)

    mask = (w0_nm >= LAMBDA_MIN_NM) & (w0_nm <= LAMBDA_MAX_NM)
    w0_nm = w0_nm[mask]
    R0 = R0[mask]

    if len(w0_nm) < 5:
        raise ValueError(f"{angle_label} 数据点太少，无法进行单角扫描。")

    lam_nm = np.linspace(np.min(w0_nm), np.max(w0_nm), N_LAMBDA)
    R0_i = np.interp(lam_nm, w0_nm, R0)
    lam = lam_nm * 1e-9

    d_grid_nm = np.arange(
        SCAN_D_MIN_NM,
        SCAN_D_MAX_NM + 1e-12,
        SCAN_D_STEP_NM
    )

    obj_curve = compute_single_angle_objective_curve(
        lam=lam,
        R_target=R0_i,
        theta_deg=THETA1,
        n0=N0,
        n1=N1,
        n2=N2,
        pol=POL,
        d_grid_nm=d_grid_nm,
    )

    best_idx = int(np.argmin(obj_curve))
    best_d_nm = float(d_grid_nm[best_idx])
    best_obj = float(obj_curve[best_idx])

    plot_single_angle_scan_0deg(
        lam_nm=lam_nm,
        R0_raw=R0_i,
        d_grid_nm=d_grid_nm,
        obj_curve=obj_curve,
        best_d_nm=best_d_nm,
        out_prefix=f"single_angle_{angle_label}_scan",
    )

    sort_idx = np.argsort(obj_curve)
    top_rows = []
    used_d = []

    for idx in sort_idx:
        d_nm = float(d_grid_nm[idx])

        if any(abs(d_nm - x) < max(1.0, 3 * SCAN_D_STEP_NM) for x in used_d):
            continue

        used_d.append(d_nm)
        top_rows.append([d_nm, float(obj_curve[idx])])

        if len(top_rows) >= 5:
            break

    save_rows_csv(
        f"single_angle_{angle_label}_scan_top_candidates.csv",
        ["thickness_nm", "objective"],
        top_rows
    )

    lines = [
        f"{angle_label} single-angle scan summary",
        f"csv_file_angle1 = {CSV_FILE_0DEG}",
        f"POL = {POL}",
        f"scan_range_nm = [{SCAN_D_MIN_NM}, {SCAN_D_MAX_NM}]",
        f"scan_step_nm = {SCAN_D_STEP_NM}",
        f"best_d_nm = {best_d_nm:.6f}",
        f"best_objective = {best_obj:.12e}",
        "",
        "Top candidate minima:",
    ]
    for row in top_rows:
        lines.append(f"d_nm = {row[0]:.6f}, objective = {row[1]:.12e}")

    save_text_report(f"single_angle_{angle_label}_scan_summary.txt", lines)

    print("=" * 90)
    print(f"{angle_label} single-angle scan")
    print("=" * 90)
    print(f"best_d_nm      = {best_d_nm:.6f}")
    print(f"best_objective = {best_obj:.12e}")
    print("Top candidate minima:")
    for row in top_rows:
        print(f"  d_nm = {row[0]:.6f}, objective = {row[1]:.12e}")


def compute_dual_objective_heatmap(
    lam: np.ndarray,
    R1: np.ndarray,
    R2: np.ndarray,
    theta1_fixed: float,
    d_grid_nm: np.ndarray,
    theta2_grid_deg: np.ndarray,
    n0: float,
    n1: float,
    n2: float,
    pol: str,
) -> np.ndarray:
    heatmap = np.zeros((len(theta2_grid_deg), len(d_grid_nm)), dtype=float)

    for i, theta2_test in enumerate(theta2_grid_deg):
        for j, d_nm in enumerate(d_grid_nm):
            err, _, _ = evaluate_dual_fit_objective(
                lam=lam,
                R1=R1,
                theta1=theta1_fixed,
                R2=R2,
                theta2=float(theta2_test),
                d=float(d_nm * 1e-9),
            n0=n0,
            n1=n1,
            n2=n2,
            pol=pol,
            mix_p_weight=MIX_P_WEIGHT,
            lambda_a=LAMBDA_A,
                lambda_b=LAMBDA_B,
                smooth_window=OBJECTIVE_SMOOTH_WINDOW,
                weight_level=OBJECTIVE_WEIGHT_LEVEL,
                weight_shape=OBJECTIVE_WEIGHT_SHAPE,
                weight_slope=OBJECTIVE_WEIGHT_SLOPE,
            )
            heatmap[i, j] = float(err)

    return heatmap


def plot_objective_heatmap_d_theta2(
    d_grid_nm: np.ndarray,
    theta2_grid_deg: np.ndarray,
    heatmap: np.ndarray,
    out_prefix: str = "objective_heatmap_d_theta2",
) -> None:
    min_idx = np.unravel_index(np.argmin(heatmap), heatmap.shape)
    best_theta2 = float(theta2_grid_deg[min_idx[0]])
    best_d_nm = float(d_grid_nm[min_idx[1]])
    best_obj = float(heatmap[min_idx])

    plt.figure(figsize=(9, 6))
    plt.imshow(
        heatmap,
        aspect="auto",
        origin="lower",
        extent=[
            float(np.min(d_grid_nm)),
            float(np.max(d_grid_nm)),
            float(np.min(theta2_grid_deg)),
            float(np.max(theta2_grid_deg)),
        ],
    )
    plt.colorbar(label="Objective")
    plt.scatter([best_d_nm], [best_theta2], marker="x", s=80, label="Global min")
    plt.xlabel("Thickness (nm)")
    plt.ylabel("Theta2 (deg)")
    plt.title("Objective heatmap: thickness vs theta2")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(d_grid_nm, heatmap[min_idx[0], :], linewidth=1.8)
    plt.axvline(best_d_nm, linestyle="--", label=f"best d = {best_d_nm:.3f} nm")
    plt.xlabel("Thickness (nm)")
    plt.ylabel("Objective")
    plt.title(f"Heatmap slice at theta2 = {best_theta2:.3f} deg")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_slice_d.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(theta2_grid_deg, heatmap[:, min_idx[1]], linewidth=1.8)
    plt.axvline(best_theta2, linestyle="--", label=f"best theta2 = {best_theta2:.3f} deg")
    plt.xlabel("Theta2 (deg)")
    plt.ylabel("Objective")
    plt.title(f"Heatmap slice at d = {best_d_nm:.3f} nm")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{out_prefix}_slice_theta2.png", dpi=200)
    plt.show()

    lines = [
        "Objective heatmap summary",
        f"best_d_nm = {best_d_nm:.6f}",
        f"best_theta2_deg = {best_theta2:.6f}",
        f"best_objective = {best_obj:.12e}",
        f"d_range_nm = [{np.min(d_grid_nm):.6f}, {np.max(d_grid_nm):.6f}]",
        f"theta2_range_deg = [{np.min(theta2_grid_deg):.6f}, {np.max(theta2_grid_deg):.6f}]",
    ]
    save_text_report("objective_heatmap_d_theta2_summary.txt", lines)

    print("=" * 90)
    print("Objective heatmap: thickness vs theta2")
    print("=" * 90)
    print(f"best_d_nm         = {best_d_nm:.6f}")
    print(f"best_theta2_deg   = {best_theta2:.6f}")
    print(f"best_objective    = {best_obj:.12e}")


def run_objective_heatmap_d_theta2() -> None:
    w1_nm, R1 = read_reflectance_csv(CSV_FILE_0DEG, y_selector=FIT_Y_SELECTOR_0DEG)
    w2_nm, R2 = read_reflectance_csv(CSV_FILE_2DEG, y_selector=FIT_Y_SELECTOR_2DEG)

    lam_nm, R1_i, R2_i = unify_two_reflectance_curves(
        w1_nm, R1, w2_nm, R2,
        wmin_nm=LAMBDA_MIN_NM,
        wmax_nm=LAMBDA_MAX_NM,
        n_lambda=N_LAMBDA
    )
    lam = lam_nm * 1e-9

    d_grid_nm = np.arange(
        HEATMAP_D_MIN_NM,
        HEATMAP_D_MAX_NM + 1e-12,
        HEATMAP_D_STEP_NM
    )
    theta2_grid_deg = np.arange(
        HEATMAP_THETA2_MIN_DEG,
        HEATMAP_THETA2_MAX_DEG + 1e-12,
        HEATMAP_THETA2_STEP_DEG
    )

    heatmap = compute_dual_objective_heatmap(
        lam=lam,
        R1=R1_i,
        R2=R2_i,
        theta1_fixed=THETA1,
        d_grid_nm=d_grid_nm,
        theta2_grid_deg=theta2_grid_deg,
        n0=N0,
        n1=N1,
        n2=N2,
        pol=POL,
    )

    save_rows_csv(
        "objective_heatmap_d_theta2_axes.csv",
        ["axis_name", "values"],
        [
            ["d_grid_nm", ";".join(f"{x:.6f}" for x in d_grid_nm)],
            ["theta2_grid_deg", ";".join(f"{x:.6f}" for x in theta2_grid_deg)],
        ]
    )

    heatmap_path = OUTPUT_DIR / "objective_heatmap_d_theta2_matrix.csv"
    pd.DataFrame(
        heatmap,
        index=[f"{x:.6f}" for x in theta2_grid_deg],
        columns=[f"{x:.6f}" for x in d_grid_nm],
    ).to_csv(heatmap_path, encoding="utf-8-sig")
    print(f"Saved csv: {heatmap_path}")

    plot_objective_heatmap_d_theta2(
        d_grid_nm=d_grid_nm,
        theta2_grid_deg=theta2_grid_deg,
        heatmap=heatmap,
        out_prefix="objective_heatmap_d_theta2",
    )


# =========================================================
# 12C. 诊断模块：固定厚度下对比指定角度的 s / p / avg
# =========================================================
def compute_error_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[float, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    return mae, rmse


def run_compare_80deg_at_fixed_d() -> None:
    w2_nm, R2 = read_reflectance_csv(CSV_FILE_2DEG, y_selector=FIT_Y_SELECTOR_2DEG)

    mask = (w2_nm >= LAMBDA_MIN_NM) & (w2_nm <= LAMBDA_MAX_NM)
    w2_nm = w2_nm[mask]
    R2 = R2[mask]

    if len(w2_nm) < 5:
        raise ValueError("数据点太少，无法进行固定厚度对比。")

    lam_nm = np.linspace(np.min(w2_nm), np.max(w2_nm), N_LAMBDA)
    R2_i = np.interp(lam_nm, w2_nm, R2)
    lam = lam_nm * 1e-9

    d_fixed = FIXED_D_COMPARE_NM * 1e-9
    theta_fixed = FIXED_THETA_COMPARE_DEG

    R_s = thinfilm_reflectance_angle(lam, N0, N1, N2, d_fixed, theta_fixed, pol="s")
    R_p = thinfilm_reflectance_angle(lam, N0, N1, N2, d_fixed, theta_fixed, pol="p")
    R_avg = thinfilm_reflectance_angle(lam, N0, N1, N2, d_fixed, theta_fixed, pol="avg")

    mae_s, rmse_s = compute_error_metrics(R2_i, R_s)
    mae_p, rmse_p = compute_error_metrics(R2_i, R_p)
    mae_avg, rmse_avg = compute_error_metrics(R2_i, R_avg)

    rows = [
        ["s", mae_s, rmse_s],
        ["p", mae_p, rmse_p],
        ["avg", mae_avg, rmse_avg],
    ]
    save_rows_csv(
        "compare_at_fixed_d_metrics.csv",
        ["model_pol", "mae", "rmse"],
        rows
    )

    metric_map = {
        "s": (mae_s, rmse_s),
        "p": (mae_p, rmse_p),
        "avg": (mae_avg, rmse_avg),
    }
    best_pol = min(metric_map, key=lambda k: metric_map[k][1])

    plt.figure(figsize=(9, 6))
    plt.plot(lam_nm, R2_i, label=f"COMSOL {theta_fixed:.1f}deg", linewidth=1.8)
    plt.plot(lam_nm, R_s, "--", label=f"Model s  (RMSE={rmse_s:.3e})", linewidth=1.6)
    plt.plot(lam_nm, R_p, "--", label=f"Model p  (RMSE={rmse_p:.3e})", linewidth=1.6)
    plt.plot(lam_nm, R_avg, "--", label=f"Model avg (RMSE={rmse_avg:.3e})", linewidth=1.6)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"{theta_fixed:.1f}deg comparison at fixed d = {FIXED_D_COMPARE_NM:.3f} nm")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "compare_at_fixed_d_overlay.png", dpi=200)
    plt.show()

    plt.figure(figsize=(9, 6))
    plt.plot(lam_nm, R2_i - R_s, label="Residual: COMSOL - s", linewidth=1.5)
    plt.plot(lam_nm, R2_i - R_p, label="Residual: COMSOL - p", linewidth=1.5)
    plt.plot(lam_nm, R2_i - R_avg, label="Residual: COMSOL - avg", linewidth=1.5)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Residual")
    plt.title(f"{theta_fixed:.1f}deg residuals at fixed d = {FIXED_D_COMPARE_NM:.3f} nm")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "compare_at_fixed_d_residuals.png", dpi=200)
    plt.show()

    if best_pol == "s":
        R_best = R_s
    elif best_pol == "p":
        R_best = R_p
    else:
        R_best = R_avg

    plt.figure(figsize=(9, 6))
    plt.plot(lam_nm, R2_i, label=f"COMSOL {theta_fixed:.1f}deg", linewidth=1.8)
    plt.plot(lam_nm, R_best, "--", label=f"Best model = {best_pol}", linewidth=2.0)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"Best {theta_fixed:.1f}deg match at fixed d = {FIXED_D_COMPARE_NM:.3f} nm")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "compare_at_fixed_d_best_only.png", dpi=200)
    plt.show()

    lines = [
        f"{theta_fixed:.1f}deg fixed-thickness comparison summary",
        f"csv_file = {CSV_FILE_2DEG}",
        f"fixed_d_nm = {FIXED_D_COMPARE_NM:.6f}",
        f"fixed_theta_deg = {FIXED_THETA_COMPARE_DEG:.6f}",
        "",
        f"s   : MAE = {mae_s:.12e}, RMSE = {rmse_s:.12e}",
        f"p   : MAE = {mae_p:.12e}, RMSE = {rmse_p:.12e}",
        f"avg : MAE = {mae_avg:.12e}, RMSE = {rmse_avg:.12e}",
        "",
        f"best_match_by_rmse = {best_pol}",
    ]
    save_text_report("compare_at_fixed_d_summary.txt", lines)

    save_json_report(
        "compare_at_fixed_d_summary.json",
        {
            "csv_file": str(CSV_FILE_2DEG),
            "fixed_d_nm": float(FIXED_D_COMPARE_NM),
            "fixed_theta_deg": float(FIXED_THETA_COMPARE_DEG),
            "metrics": {
                "s": {"mae": mae_s, "rmse": rmse_s},
                "p": {"mae": mae_p, "rmse": rmse_p},
                "avg": {"mae": mae_avg, "rmse": rmse_avg},
            },
            "best_match_by_rmse": best_pol,
        }
    )

    print("=" * 90)
    print("Angle comparison at fixed thickness")
    print("=" * 90)
    print(f"fixed_d_nm       = {FIXED_D_COMPARE_NM:.6f}")
    print(f"fixed_theta_deg  = {FIXED_THETA_COMPARE_DEG:.6f}")
    print(f"s   -> MAE = {mae_s:.12e}, RMSE = {rmse_s:.12e}")
    print(f"p   -> MAE = {mae_p:.12e}, RMSE = {rmse_p:.12e}")
    print(f"avg -> MAE = {mae_avg:.12e}, RMSE = {rmse_avg:.12e}")
    print(f"best_match_by_rmse = {best_pol}")


# =========================================================
# 12D. 诊断模块：固定厚度，只扫描 theta2
# =========================================================
def run_theta2_scan_at_fixed_d() -> None:
    w2_nm, R2 = read_reflectance_csv(CSV_FILE_2DEG, y_selector=FIT_Y_SELECTOR_2DEG)

    mask = (w2_nm >= LAMBDA_MIN_NM) & (w2_nm <= LAMBDA_MAX_NM)
    w2_nm = w2_nm[mask]
    R2 = R2[mask]

    if len(w2_nm) < 5:
        raise ValueError("数据点太少，无法进行 theta2 扫描。")

    lam_nm = np.linspace(np.min(w2_nm), np.max(w2_nm), N_LAMBDA)
    R2_i = np.interp(lam_nm, w2_nm, R2)
    lam = lam_nm * 1e-9

    d_fixed_nm = THETA2_SCAN_FIXED_D_NM
    d_fixed = d_fixed_nm * 1e-9

    theta_grid = np.arange(
        THETA2_SCAN_MIN_DEG,
        THETA2_SCAN_MAX_DEG + 1e-12,
        THETA2_SCAN_STEP_DEG
    )

    rows = []
    best_theta = None
    best_rmse = np.inf
    best_mae = np.inf
    best_curve = None

    for theta in theta_grid:
        R_model = thinfilm_reflectance_angle(
            lam, N0, N1, N2, d_fixed, theta, pol=THETA2_SCAN_POL
        )

        mae = float(np.mean(np.abs(R2_i - R_model)))
        rmse = float(np.sqrt(np.mean((R2_i - R_model) ** 2)))

        rows.append([float(theta), mae, rmse])

        if rmse < best_rmse:
            best_theta = float(theta)
            best_mae = mae
            best_rmse = rmse
            best_curve = R_model.copy()

    save_rows_csv(
        "theta2_scan_at_fixed_d.csv",
        ["theta2_deg", "mae", "rmse"],
        rows
    )

    theta_vals = np.array([r[0] for r in rows], dtype=float)
    mae_vals = np.array([r[1] for r in rows], dtype=float)
    rmse_vals = np.array([r[2] for r in rows], dtype=float)

    plt.figure(figsize=(8, 5))
    plt.plot(theta_vals, rmse_vals, linewidth=1.8, label="RMSE")
    plt.axvline(best_theta, linestyle="--", label=f"best theta = {best_theta:.3f} deg")
    plt.xlabel("Theta2 (deg)")
    plt.ylabel("RMSE")
    plt.title(f"Theta2 scan at fixed d = {d_fixed_nm:.3f} nm, pol = {THETA2_SCAN_POL}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "theta2_scan_at_fixed_d_rmse.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(theta_vals, mae_vals, linewidth=1.8, label="MAE")
    plt.axvline(best_theta, linestyle="--", label=f"best theta = {best_theta:.3f} deg")
    plt.xlabel("Theta2 (deg)")
    plt.ylabel("MAE")
    plt.title(f"Theta2 scan at fixed d = {d_fixed_nm:.3f} nm, pol = {THETA2_SCAN_POL}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "theta2_scan_at_fixed_d_mae.png", dpi=200)
    plt.show()

    plt.figure(figsize=(9, 6))
    plt.plot(lam_nm, R2_i, label=f"COMSOL {FIXED_THETA_COMPARE_DEG:.1f}deg", linewidth=1.8)
    plt.plot(lam_nm, best_curve, "--", label=f"Model best theta = {best_theta:.3f} deg", linewidth=2.0)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance")
    plt.title(f"Best theta2 match at fixed d = {d_fixed_nm:.3f} nm, pol = {THETA2_SCAN_POL}")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "theta2_scan_at_fixed_d_best_fit.png", dpi=200)
    plt.show()

    plt.figure(figsize=(9, 6))
    plt.plot(lam_nm, R2_i - best_curve, linewidth=1.6)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Residual")
    plt.title(f"Residual at best theta2 = {best_theta:.3f} deg")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "theta2_scan_at_fixed_d_best_residual.png", dpi=200)
    plt.show()

    lines = [
        "Theta2 scan at fixed thickness summary",
        f"csv_file = {CSV_FILE_2DEG}",
        f"fixed_d_nm = {d_fixed_nm:.6f}",
        f"pol = {THETA2_SCAN_POL}",
        f"theta2_scan_range_deg = [{THETA2_SCAN_MIN_DEG:.6f}, {THETA2_SCAN_MAX_DEG:.6f}]",
        f"theta2_scan_step_deg = {THETA2_SCAN_STEP_DEG:.6f}",
        "",
        f"best_theta2_deg = {best_theta:.6f}",
        f"best_mae = {best_mae:.12e}",
        f"best_rmse = {best_rmse:.12e}",
    ]
    save_text_report("theta2_scan_at_fixed_d_summary.txt", lines)

    save_json_report(
        "theta2_scan_at_fixed_d_summary.json",
        {
            "csv_file": str(CSV_FILE_2DEG),
            "fixed_d_nm": float(d_fixed_nm),
            "pol": THETA2_SCAN_POL,
            "theta2_scan_min_deg": float(THETA2_SCAN_MIN_DEG),
            "theta2_scan_max_deg": float(THETA2_SCAN_MAX_DEG),
            "theta2_scan_step_deg": float(THETA2_SCAN_STEP_DEG),
            "best_theta2_deg": float(best_theta),
            "best_mae": float(best_mae),
            "best_rmse": float(best_rmse),
        }
    )

    print("=" * 90)
    print("Theta2 scan at fixed thickness")
    print("=" * 90)
    print(f"fixed_d_nm      = {d_fixed_nm:.6f}")
    print(f"pol             = {THETA2_SCAN_POL}")
    print(f"best_theta2_deg = {best_theta:.6f}")
    print(f"best_mae        = {best_mae:.12e}")
    print(f"best_rmse       = {best_rmse:.12e}")


# =========================================================
# 13. 批处理
# =========================================================
def find_batch_pairs(input_dir: Path, label_1: str, label_2: str) -> List[Tuple[str, Path, Path]]:
    input_dir = Path(input_dir)
    if not input_dir.exists():
        raise FileNotFoundError(f"批量输入目录不存在: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"BATCH_INPUT_DIR 必须是文件夹，而不是单个文件: {input_dir}")

    pattern_1 = f"*_{label_1}.csv"
    files_1 = sorted(input_dir.glob(pattern_1))

    pairs: List[Tuple[str, Path, Path]] = []
    missing: List[Tuple[str, str]] = []

    for f1 in files_1:
        suffix = f"_{label_1}.csv"
        if not f1.name.endswith(suffix):
            continue

        sample_id = f1.name[:-len(suffix)]
        f2 = input_dir / f"{sample_id}_{label_2}.csv"

        if f2.exists():
            pairs.append((sample_id, f1, f2))
        else:
            missing.append((sample_id, str(f2)))

    if missing:
        print("=" * 80)
        print("Warning: 以下样品缺少配对文件")
        for sid, miss_path in missing:
            print(f"  sample_id = {sid}, missing = {miss_path}")
        print("=" * 80)

    return pairs


def run_batch_fit_csv() -> None:
    print("=" * 100)
    print("Batch fit CSV with theta2 search")
    print("=" * 100)
    print(f"BATCH_INPUT_DIR = {BATCH_INPUT_DIR}")
    print(f"BATCH_LABEL_1   = {BATCH_LABEL_1}")
    print(f"BATCH_LABEL_2   = {BATCH_LABEL_2}")

    pairs = find_batch_pairs(BATCH_INPUT_DIR, BATCH_LABEL_1, BATCH_LABEL_2)

    if len(pairs) == 0:
        print("没有找到可用的成对 CSV 文件。")
        return

    results: List[Dict] = []

    for i, (sample_id, f1, f2) in enumerate(pairs, start=1):
        print("\n" + "-" * 100)
        print(f"[{i}/{len(pairs)}] sample_id = {sample_id}")
        print(f"  file1 = {f1}")
        print(f"  file2 = {f2}")

        try:
            result = fit_dual_csv_with_theta2_search_from_files(
                f1, f2, sample_id=sample_id, save_plots=False
            )
            results.append(result)

            print(f"  theta2_fit            = {result['theta2_fit_deg']:.3f} deg")
            print(f"  d_fit_nominal         = {result['d_fit_nominal_nm']:.3f} nm")
            print(f"  d_fit_corrected       = {result['d_fit_corrected_nm']:.3f} nm")
            print(f"  d_fit_nominal_cal     = {result['d_fit_nominal_calibrated_nm']:.3f} nm")
            print(f"  d_fit_corrected_cal   = {result['d_fit_corrected_calibrated_nm']:.3f} nm")
            print(f"  delta_d               = {result['delta_d_nm']:.3f} nm")
            print(f"  objective             = {result['best_objective']:.6e}")

        except Exception as e:
            print(f"  ERROR for sample {sample_id}: {e}")

    if len(results) == 0:
        print("所有样品都处理失败。")
        return

    summary_rows = []
    for r in results:
        summary_rows.append([
            r["sample_id"],
            r["theta1_fixed_deg"],
            r["theta2_nominal_deg"],
            r["theta2_fit_deg"],
            r["d_fit_nominal_nm"],
            r["d_fit_corrected_nm"],
            r["d_fit_nominal_calibrated_nm"],
            r["d_fit_corrected_calibrated_nm"],
            r["delta_d_nm"],
            r["best_objective"],
            r["csv_file_1"],
            r["csv_file_2"],
        ])

    save_rows_csv(
        "batch_fit_summary.csv",
        [
            "sample_id",
            "theta1_fixed_deg",
            "theta2_nominal_deg",
            "theta2_fit_deg",
            "d_fit_nominal_nm",
            "d_fit_corrected_nm",
            "d_fit_nominal_calibrated_nm",
            "d_fit_corrected_calibrated_nm",
            "delta_d_nm",
            "best_objective",
            "csv_file_1",
            "csv_file_2",
        ],
        summary_rows,
    )

    save_json_report("batch_fit_summary.json", {"results": results})

    lines = [
        "Batch fit summary",
        f"input_dir = {BATCH_INPUT_DIR}",
        f"n_samples = {len(results)}",
        "",
    ]

    theta2_fit_list = [r["theta2_fit_deg"] for r in results]
    d_nominal_list = [r["d_fit_nominal_calibrated_nm"] for r in results]
    d_corrected_list = [r["d_fit_corrected_calibrated_nm"] for r in results]

    lines.append(f"theta2_fit_mean = {np.mean(theta2_fit_list):.6f} deg")
    lines.append(f"theta2_fit_std  = {np.std(theta2_fit_list):.6f} deg")
    lines.append(f"d_nominal_mean  = {np.mean(d_nominal_list):.6f} nm")
    lines.append(f"d_corrected_mean= {np.mean(d_corrected_list):.6f} nm")
    lines.append("")

    for r in results:
        lines.append(
            f"{r['sample_id']}: "
            f"theta2_fit={r['theta2_fit_deg']:.3f} deg, "
            f"d_nominal={r['d_fit_nominal_nm']:.3f} nm, "
            f"d_corrected={r['d_fit_corrected_nm']:.3f} nm, "
            f"delta_d={r['delta_d_nm']:.3f} nm"
        )

    save_text_report("batch_fit_summary.txt", lines)

    sample_ids = [r["sample_id"] for r in results]
    x = np.arange(len(sample_ids))
    d_nominal = np.array([r["d_fit_nominal_calibrated_nm"] for r in results])
    d_corrected = np.array([r["d_fit_corrected_calibrated_nm"] for r in results])
    theta2_fit = np.array([r["theta2_fit_deg"] for r in results])

    plt.figure(figsize=(10, 5))
    plt.plot(x, d_nominal, marker="o", label="d nominal")
    plt.plot(x, d_corrected, marker="o", label="d corrected")
    plt.xticks(x, sample_ids, rotation=30)
    plt.xlabel("Sample ID")
    plt.ylabel("Thickness (nm)")
    plt.title("Batch thickness fit summary")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_fit_thickness_summary.png", dpi=200)
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.plot(x, theta2_fit, marker="o", label="theta2 fit")
    plt.axhline(THETA2, linestyle="--", label="theta2 nominal")
    plt.xticks(x, sample_ids, rotation=30)
    plt.xlabel("Sample ID")
    plt.ylabel("Angle (deg)")
    plt.title("Batch theta2 fit summary")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_fit_theta2_summary.png", dpi=200)
    plt.show()


# =========================================================
# 14. 运行入口
# =========================================================
def parse_true_thickness_nm_from_sample_id(sample_id: str) -> float:
    text = str(sample_id).strip()
    m = re.search(TRUE_THICKNESS_REGEX, text, flags=re.IGNORECASE)
    if m:
        return float(m.group(1))

    if TRUE_THICKNESS_FALLBACK_FIRST_NUMBER:
        m = re.search(r"(\d+(?:\.\d+)?)", text)
        if m:
            return float(m.group(1))

    raise ValueError(
        f"Cannot infer true thickness from sample_id={sample_id!r}. "
        f"Current regex={TRUE_THICKNESS_REGEX!r}"
    )


def run_batch_fit_core() -> List[Dict]:
    print("=" * 100)
    print("Batch fit CSV with theta2 search")
    print("=" * 100)
    print(f"BATCH_INPUT_DIR = {BATCH_INPUT_DIR}")
    print(f"BATCH_LABEL_1   = {BATCH_LABEL_1}")
    print(f"BATCH_LABEL_2   = {BATCH_LABEL_2}")

    pairs = find_batch_pairs(BATCH_INPUT_DIR, BATCH_LABEL_1, BATCH_LABEL_2)
    if len(pairs) == 0:
        print("No usable paired CSV files were found.")
        return []

    results: List[Dict] = []
    for i, (sample_id, f1, f2) in enumerate(pairs, start=1):
        print("\n" + "-" * 100)
        print(f"[{i}/{len(pairs)}] sample_id = {sample_id}")
        print(f"  file1 = {f1}")
        print(f"  file2 = {f2}")

        try:
            result = fit_dual_csv_with_theta2_search_from_files(
                f1, f2, sample_id=sample_id, save_plots=False
            )
            results.append(result)
            print(f"  theta2_fit            = {result['theta2_fit_deg']:.3f} deg")
            print(f"  d_fit_nominal         = {result['d_fit_nominal_nm']:.3f} nm")
            print(f"  d_fit_corrected       = {result['d_fit_corrected_nm']:.3f} nm")
            print(f"  d_fit_nominal_cal     = {result['d_fit_nominal_calibrated_nm']:.3f} nm")
            print(f"  d_fit_corrected_cal   = {result['d_fit_corrected_calibrated_nm']:.3f} nm")
            print(f"  delta_d               = {result['delta_d_nm']:.3f} nm")
            print(f"  objective             = {result['best_objective']:.6e}")
        except Exception as e:
            print(f"  ERROR for sample {sample_id}: {e}")

    if len(results) == 0:
        print("All samples failed during batch fitting.")
        return []

    return results


def save_batch_fit_summary_outputs(results: List[Dict]) -> None:
    if len(results) == 0:
        return

    summary_rows = []
    for r in results:
        summary_rows.append([
            r["sample_id"],
            r["theta1_fixed_deg"],
            r["theta2_nominal_deg"],
            r["theta2_fit_deg"],
            r["d_fit_nominal_nm"],
            r["d_fit_corrected_nm"],
            r["d_fit_nominal_calibrated_nm"],
            r["d_fit_corrected_calibrated_nm"],
            r["delta_d_nm"],
            r["best_objective"],
            r["csv_file_1"],
            r["csv_file_2"],
        ])

    save_rows_csv(
        "batch_fit_summary.csv",
        [
            "sample_id",
            "theta1_fixed_deg",
            "theta2_nominal_deg",
            "theta2_fit_deg",
            "d_fit_nominal_nm",
            "d_fit_corrected_nm",
            "d_fit_nominal_calibrated_nm",
            "d_fit_corrected_calibrated_nm",
            "delta_d_nm",
            "best_objective",
            "csv_file_1",
            "csv_file_2",
        ],
        summary_rows,
    )
    save_json_report("batch_fit_summary.json", {"results": results})

    lines = [
        "Batch fit summary",
        f"input_dir = {BATCH_INPUT_DIR}",
        f"n_samples = {len(results)}",
        "",
    ]
    theta2_fit_list = [r["theta2_fit_deg"] for r in results]
    d_nominal_list = [r["d_fit_nominal_calibrated_nm"] for r in results]
    d_corrected_list = [r["d_fit_corrected_calibrated_nm"] for r in results]
    lines.append(f"theta2_fit_mean = {np.mean(theta2_fit_list):.6f} deg")
    lines.append(f"theta2_fit_std  = {np.std(theta2_fit_list):.6f} deg")
    lines.append(f"d_nominal_mean  = {np.mean(d_nominal_list):.6f} nm")
    lines.append(f"d_corrected_mean= {np.mean(d_corrected_list):.6f} nm")
    lines.append("")

    for r in results:
        lines.append(
            f"{r['sample_id']}: "
            f"theta2_fit={r['theta2_fit_deg']:.3f} deg, "
            f"d_nominal={r['d_fit_nominal_nm']:.3f} nm, "
            f"d_corrected={r['d_fit_corrected_nm']:.3f} nm, "
            f"delta_d={r['delta_d_nm']:.3f} nm"
        )

    save_text_report("batch_fit_summary.txt", lines)

    sample_ids = [r["sample_id"] for r in results]
    x = np.arange(len(sample_ids))
    d_nominal = np.array([r["d_fit_nominal_calibrated_nm"] for r in results])
    d_corrected = np.array([r["d_fit_corrected_calibrated_nm"] for r in results])
    theta2_fit = np.array([r["theta2_fit_deg"] for r in results])

    plt.figure(figsize=(10, 5))
    plt.plot(x, d_nominal, marker="o", label="d nominal")
    plt.plot(x, d_corrected, marker="o", label="d corrected")
    plt.xticks(x, sample_ids, rotation=30)
    plt.xlabel("Sample ID")
    plt.ylabel("Thickness (nm)")
    plt.title("Batch thickness fit summary")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_fit_thickness_summary.png", dpi=200)
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.plot(x, theta2_fit, marker="o", label="theta2 fit")
    plt.axhline(THETA2, linestyle="--", label="theta2 nominal")
    plt.xticks(x, sample_ids, rotation=30)
    plt.xlabel("Sample ID")
    plt.ylabel("Angle (deg)")
    plt.title("Batch theta2 fit summary")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_fit_theta2_summary.png", dpi=200)
    plt.show()


def compute_error_statistics(values: np.ndarray) -> Dict[str, float]:
    values = np.asarray(values, dtype=float).ravel()
    return {
        "mean_error_nm": float(np.mean(values)),
        "mae_nm": float(np.mean(np.abs(values))),
        "rmse_nm": float(np.sqrt(np.mean(values ** 2))),
        "std_nm": float(np.std(values)),
        "max_abs_error_nm": float(np.max(np.abs(values))),
    }


def save_batch_error_analysis_outputs(results: List[Dict]) -> None:
    if len(results) == 0:
        return

    rows = []
    for r in results:
        true_nm = parse_true_thickness_nm_from_sample_id(r["sample_id"])
        err_nominal = float(r["d_fit_nominal_calibrated_nm"] - true_nm)
        err_corrected = float(r["d_fit_corrected_calibrated_nm"] - true_nm)
        rows.append({
            "sample_id": r["sample_id"],
            "true_thickness_nm": true_nm,
            "theta2_fit_deg": float(r["theta2_fit_deg"]),
            "theta2_nominal_deg": float(r["theta2_nominal_deg"]),
            "theta2_shift_deg": float(r["theta2_fit_deg"] - r["theta2_nominal_deg"]),
            "d_fit_nominal_nm": float(r["d_fit_nominal_nm"]),
            "d_fit_corrected_nm": float(r["d_fit_corrected_nm"]),
            "d_fit_nominal_calibrated_nm": float(r["d_fit_nominal_calibrated_nm"]),
            "d_fit_corrected_calibrated_nm": float(r["d_fit_corrected_calibrated_nm"]),
            "error_nominal_nm": err_nominal,
            "error_corrected_nm": err_corrected,
            "abs_error_nominal_nm": abs(err_nominal),
            "abs_error_corrected_nm": abs(err_corrected),
            "delta_d_nm": float(r["delta_d_nm"]),
            "best_objective": float(r["best_objective"]),
            "csv_file_1": r["csv_file_1"],
            "csv_file_2": r["csv_file_2"],
        })

    rows = sorted(rows, key=lambda x: x["true_thickness_nm"])
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "batch_error_analysis.csv", index=False, encoding="utf-8-sig")

    nominal_stats = compute_error_statistics(df["error_nominal_nm"].to_numpy())
    corrected_stats = compute_error_statistics(df["error_corrected_nm"].to_numpy())
    theta_shift = df["theta2_shift_deg"].to_numpy(dtype=float)
    theta_stats = {
        "mean_shift_deg": float(np.mean(theta_shift)),
        "std_shift_deg": float(np.std(theta_shift)),
        "max_abs_shift_deg": float(np.max(np.abs(theta_shift))),
    }

    save_json_report(
        "batch_error_analysis.json",
        {
            "input_dir": str(BATCH_INPUT_DIR),
            "n_samples": int(len(df)),
            "true_thickness_regex": TRUE_THICKNESS_REGEX,
            "nominal_fit_stats": nominal_stats,
            "corrected_fit_stats": corrected_stats,
            "theta2_shift_stats": theta_stats,
            "results": rows,
        },
    )

    lines = [
        "Batch error analysis",
        f"input_dir = {BATCH_INPUT_DIR}",
        f"n_samples = {len(df)}",
        f"true_thickness_regex = {TRUE_THICKNESS_REGEX}",
        "",
        "Corrected thickness error stats:",
        f"mean_error_nm = {corrected_stats['mean_error_nm']:.6f}",
        f"mae_nm = {corrected_stats['mae_nm']:.6f}",
        f"rmse_nm = {corrected_stats['rmse_nm']:.6f}",
        f"std_nm = {corrected_stats['std_nm']:.6f}",
        f"max_abs_error_nm = {corrected_stats['max_abs_error_nm']:.6f}",
        "",
        "Nominal thickness error stats:",
        f"mean_error_nm = {nominal_stats['mean_error_nm']:.6f}",
        f"mae_nm = {nominal_stats['mae_nm']:.6f}",
        f"rmse_nm = {nominal_stats['rmse_nm']:.6f}",
        f"std_nm = {nominal_stats['std_nm']:.6f}",
        f"max_abs_error_nm = {nominal_stats['max_abs_error_nm']:.6f}",
        "",
        "Theta2 shift stats:",
        f"mean_shift_deg = {theta_stats['mean_shift_deg']:.6f}",
        f"std_shift_deg = {theta_stats['std_shift_deg']:.6f}",
        f"max_abs_shift_deg = {theta_stats['max_abs_shift_deg']:.6f}",
        "",
    ]

    for row in rows:
        lines.append(
            f"{row['sample_id']}: true={row['true_thickness_nm']:.3f} nm, "
            f"d_corr={row['d_fit_corrected_calibrated_nm']:.3f} nm, "
            f"err={row['error_corrected_nm']:.3f} nm, "
            f"theta2_fit={row['theta2_fit_deg']:.4f} deg, "
            f"obj={row['best_objective']:.6e}"
        )

    save_text_report("batch_error_analysis.txt", lines)

    true_nm = df["true_thickness_nm"].to_numpy(dtype=float)
    d_corr = df["d_fit_corrected_calibrated_nm"].to_numpy(dtype=float)
    d_nom = df["d_fit_nominal_calibrated_nm"].to_numpy(dtype=float)
    err_corr = df["error_corrected_nm"].to_numpy(dtype=float)
    err_nom = df["error_nominal_nm"].to_numpy(dtype=float)
    theta_fit = df["theta2_fit_deg"].to_numpy(dtype=float)

    x = np.arange(len(df))
    labels = [str(v) for v in df["sample_id"].tolist()]

    plt.figure(figsize=(8, 6))
    mn = float(min(np.min(true_nm), np.min(d_corr), np.min(d_nom)))
    mx = float(max(np.max(true_nm), np.max(d_corr), np.max(d_nom)))
    plt.plot([mn, mx], [mn, mx], "--", label="ideal")
    plt.scatter(true_nm, d_nom, label="nominal fit", s=50)
    plt.scatter(true_nm, d_corr, label="corrected fit", s=50)
    plt.xlabel("True thickness (nm)")
    plt.ylabel("Fitted thickness (nm)")
    plt.title("True vs fitted thickness")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_error_true_vs_fit.png", dpi=200)
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.plot(x, err_nom, marker="o", label="nominal error")
    plt.plot(x, err_corr, marker="o", label="corrected error")
    plt.axhline(0.0, linestyle="--", color="k")
    plt.xticks(x, labels, rotation=30)
    plt.xlabel("Sample ID")
    plt.ylabel("Thickness error (nm)")
    plt.title("Thickness error by sample")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_error_by_sample.png", dpi=200)
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.plot(x, theta_fit, marker="o", label="theta2 fit")
    plt.axhline(THETA2, linestyle="--", label="theta2 nominal")
    plt.xticks(x, labels, rotation=30)
    plt.xlabel("Sample ID")
    plt.ylabel("Angle (deg)")
    plt.title("Theta2 fit by sample")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "batch_error_theta2_fit.png", dpi=200)
    plt.show()


def run_batch_fit_csv() -> None:
    results = run_batch_fit_core()
    save_batch_fit_summary_outputs(results)


def run_batch_error_analysis() -> None:
    results = run_batch_fit_core()
    save_batch_fit_summary_outputs(results)
    save_batch_error_analysis_outputs(results)


def optimize_thickness_for_fixed_configuration(
    lam: np.ndarray,
    R1: np.ndarray,
    theta1: float,
    R2: np.ndarray,
    theta2: float,
    n0: float,
    n1: float,
    n2: float,
    pol: str,
    mix_p_weight: float,
    d_min: float,
    d_max: float,
    lambda_a: float,
    lambda_b: float,
    n_grid: int = 400,
) -> Dict[str, Union[float, Tuple[float, float, float, float], Dict]]:
    d_grid_nm = np.linspace(float(d_min * 1e9), float(d_max * 1e9), n_grid)

    best_idx = 0
    best_err = None
    best_baseline = None
    best_metrics = None
    for idx, d_nm in enumerate(d_grid_nm):
        err, baseline_params, metrics = evaluate_dual_fit_objective(
            lam=lam,
            R1=R1,
            theta1=theta1,
            R2=R2,
            theta2=theta2,
            d=float(d_nm * 1e-9),
            n0=n0,
            n1=n1,
            n2=n2,
            pol=pol,
            mix_p_weight=mix_p_weight,
            lambda_a=lambda_a,
            lambda_b=lambda_b,
            smooth_window=OBJECTIVE_SMOOTH_WINDOW,
            weight_level=OBJECTIVE_WEIGHT_LEVEL,
            weight_shape=OBJECTIVE_WEIGHT_SHAPE,
            weight_slope=OBJECTIVE_WEIGHT_SLOPE,
        )
        if best_err is None or err < best_err:
            best_idx = idx
            best_err = float(err)
            best_baseline = baseline_params
            best_metrics = metrics

    center_nm = float(d_grid_nm[best_idx])
    step_nm = float(d_grid_nm[1] - d_grid_nm[0]) if len(d_grid_nm) >= 2 else 1.0
    left_nm = max(float(d_min * 1e9), center_nm - max(5.0, 5.0 * step_nm))
    right_nm = min(float(d_max * 1e9), center_nm + max(5.0, 5.0 * step_nm))

    if right_nm > left_nm:
        res = minimize_scalar(
            lambda d_nm: evaluate_dual_fit_objective(
                lam=lam,
                R1=R1,
                theta1=theta1,
                R2=R2,
                theta2=theta2,
                d=float(d_nm * 1e-9),
                n0=n0,
                n1=n1,
                n2=n2,
                pol=pol,
                mix_p_weight=mix_p_weight,
                lambda_a=lambda_a,
                lambda_b=lambda_b,
                smooth_window=OBJECTIVE_SMOOTH_WINDOW,
                weight_level=OBJECTIVE_WEIGHT_LEVEL,
                weight_shape=OBJECTIVE_WEIGHT_SHAPE,
                weight_slope=OBJECTIVE_WEIGHT_SLOPE,
            )[0],
            bounds=(left_nm, right_nm),
            method="bounded",
            options={"xatol": 1e-3},
        )
        best_err, best_baseline, best_metrics = evaluate_dual_fit_objective(
            lam=lam,
            R1=R1,
            theta1=theta1,
            R2=R2,
            theta2=theta2,
            d=float(res.x * 1e-9),
            n0=n0,
            n1=n1,
            n2=n2,
            pol=pol,
            mix_p_weight=mix_p_weight,
            lambda_a=lambda_a,
            lambda_b=lambda_b,
            smooth_window=OBJECTIVE_SMOOTH_WINDOW,
            weight_level=OBJECTIVE_WEIGHT_LEVEL,
            weight_shape=OBJECTIVE_WEIGHT_SHAPE,
            weight_slope=OBJECTIVE_WEIGHT_SLOPE,
        )
        center_nm = float(res.x)

    return {
        "d_fit_nm": float(center_nm),
        "best_objective": float(best_err),
        "baseline_params": tuple(float(x) for x in best_baseline),
        "metrics": best_metrics,
    }


def fit_linear_sensitivity(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if len(x) < 2:
        return 0.0, float(y[0]) if len(y) == 1 else 0.0
    slope, intercept = np.polyfit(x, y, deg=1)
    return float(slope), float(intercept)


def infer_true_thickness_for_single_sample() -> Optional[float]:
    if SINGLE_SAMPLE_TRUE_THICKNESS_NM is not None:
        return float(SINGLE_SAMPLE_TRUE_THICKNESS_NM)
    return None


def run_single_sample_error_analysis() -> None:
    true_thickness_nm = infer_true_thickness_for_single_sample()
    result = fit_dual_csv_with_theta2_search_from_files(
        CSV_FILE_0DEG,
        CSV_FILE_2DEG,
        sample_id=SINGLE_SAMPLE_REPORT_ID,
        save_plots=False,
    )
    mix_p_weight_base = float(result.get("mix_p_weight_fit", MIX_P_WEIGHT))

    spec_1 = load_reflectance_spec(CSV_FILE_0DEG, y_selector=FIT_Y_SELECTOR_0DEG)
    spec_2 = load_reflectance_spec(CSV_FILE_2DEG, y_selector=FIT_Y_SELECTOR_2DEG)
    validate_dual_fit_inputs(spec_1, THETA1, spec_2, THETA2)
    lam_nm, R1_i, R2_i = unify_two_reflectance_curves(
        spec_1.x_nm, spec_1.y, spec_2.x_nm, spec_2.y,
        wmin_nm=LAMBDA_MIN_NM,
        wmax_nm=LAMBDA_MAX_NM,
        n_lambda=N_LAMBDA,
    )
    lam = lam_nm * 1e-9

    theta_center = float(result["theta2_fit_deg"])
    theta_values = np.arange(
        theta_center - SINGLE_SAMPLE_THETA2_HALF_RANGE_DEG,
        theta_center + SINGLE_SAMPLE_THETA2_HALF_RANGE_DEG + 1e-12,
        SINGLE_SAMPLE_THETA2_STEP_DEG,
    )
    theta_rows = []
    for theta2_test in theta_values:
        opt = optimize_thickness_for_fixed_configuration(
            lam=lam,
            R1=R1_i,
            theta1=THETA1,
            R2=R2_i,
            theta2=float(theta2_test),
            n0=N0,
            n1=N1,
            n2=N2,
            pol=POL,
            mix_p_weight=mix_p_weight_base,
            d_min=D_MIN,
            d_max=D_MAX,
            lambda_a=LAMBDA_A,
            lambda_b=LAMBDA_B,
        )
        theta_rows.append({
            "theta2_deg": float(theta2_test),
            "d_fit_nm": float(opt["d_fit_nm"]),
            "best_objective": float(opt["best_objective"]),
        })

    n1_values = np.linspace(
        N1 * (1.0 - SINGLE_SAMPLE_N1_RELATIVE_HALF_RANGE),
        N1 * (1.0 + SINGLE_SAMPLE_N1_RELATIVE_HALF_RANGE),
        SINGLE_SAMPLE_N_SCAN_POINTS,
    )
    n1_rows = []
    for n1_test in n1_values:
        opt = optimize_thickness_for_fixed_configuration(
            lam=lam,
            R1=R1_i,
            theta1=THETA1,
            R2=R2_i,
            theta2=theta_center,
            n0=N0,
            n1=float(n1_test),
            n2=N2,
            pol=POL,
            mix_p_weight=mix_p_weight_base,
            d_min=D_MIN,
            d_max=D_MAX,
            lambda_a=LAMBDA_A,
            lambda_b=LAMBDA_B,
        )
        n1_rows.append({
            "n1": float(n1_test),
            "d_fit_nm": float(opt["d_fit_nm"]),
            "best_objective": float(opt["best_objective"]),
        })

    n2_values = np.linspace(
        N2 * (1.0 - SINGLE_SAMPLE_N2_RELATIVE_HALF_RANGE),
        N2 * (1.0 + SINGLE_SAMPLE_N2_RELATIVE_HALF_RANGE),
        SINGLE_SAMPLE_N_SCAN_POINTS,
    )
    n2_rows = []
    for n2_test in n2_values:
        opt = optimize_thickness_for_fixed_configuration(
            lam=lam,
            R1=R1_i,
            theta1=THETA1,
            R2=R2_i,
            theta2=theta_center,
            n0=N0,
            n1=N1,
            n2=float(n2_test),
            pol=POL,
            mix_p_weight=mix_p_weight_base,
            d_min=D_MIN,
            d_max=D_MAX,
            lambda_a=LAMBDA_A,
            lambda_b=LAMBDA_B,
        )
        n2_rows.append({
            "n2": float(n2_test),
            "d_fit_nm": float(opt["d_fit_nm"]),
            "best_objective": float(opt["best_objective"]),
        })

    theta_df = pd.DataFrame(theta_rows)
    n1_df = pd.DataFrame(n1_rows)
    n2_df = pd.DataFrame(n2_rows)

    theta_slope, _ = fit_linear_sensitivity(theta_df["theta2_deg"], theta_df["d_fit_nm"])
    n1_slope, _ = fit_linear_sensitivity(n1_df["n1"], n1_df["d_fit_nm"])
    n2_slope, _ = fit_linear_sensitivity(n2_df["n2"], n2_df["d_fit_nm"])

    corrected_fit_nm = float(result["d_fit_corrected_calibrated_nm"])
    corrected_error_nm = None if true_thickness_nm is None else float(corrected_fit_nm - true_thickness_nm)

    equivalent_theta_shift = None
    equivalent_n1_shift = None
    equivalent_n2_shift = None
    if corrected_error_nm is not None:
        if abs(theta_slope) > 1e-12:
            equivalent_theta_shift = float(corrected_error_nm / theta_slope)
        if abs(n1_slope) > 1e-12:
            equivalent_n1_shift = float(corrected_error_nm / n1_slope)
        if abs(n2_slope) > 1e-12:
            equivalent_n2_shift = float(corrected_error_nm / n2_slope)

    theta_df.to_csv(OUTPUT_DIR / "single_sample_theta2_sensitivity.csv", index=False, encoding="utf-8-sig")
    n1_df.to_csv(OUTPUT_DIR / "single_sample_n1_sensitivity.csv", index=False, encoding="utf-8-sig")
    n2_df.to_csv(OUTPUT_DIR / "single_sample_n2_sensitivity.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(8, 5))
    plt.plot(theta_df["theta2_deg"], theta_df["d_fit_nm"], marker="o")
    plt.axvline(theta_center, linestyle="--", label=f"best theta2 = {theta_center:.4f} deg")
    plt.xlabel("Theta2 (deg)")
    plt.ylabel("Re-fitted thickness (nm)")
    plt.title("Single-sample sensitivity: theta2")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "single_sample_theta2_sensitivity.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(n1_df["n1"], n1_df["d_fit_nm"], marker="o")
    plt.axvline(N1, linestyle="--", label=f"base n1 = {N1:.4f}")
    plt.xlabel("n1")
    plt.ylabel("Re-fitted thickness (nm)")
    plt.title("Single-sample sensitivity: n1")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "single_sample_n1_sensitivity.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(n2_df["n2"], n2_df["d_fit_nm"], marker="o")
    plt.axvline(N2, linestyle="--", label=f"base n2 = {N2:.4f}")
    plt.xlabel("n2")
    plt.ylabel("Re-fitted thickness (nm)")
    plt.title("Single-sample sensitivity: n2")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "single_sample_n2_sensitivity.png", dpi=200)
    plt.show()

    payload = {
        "sample_id": SINGLE_SAMPLE_REPORT_ID,
        "csv_file_1": str(CSV_FILE_0DEG),
        "csv_file_2": str(CSV_FILE_2DEG),
        "true_thickness_nm": true_thickness_nm,
        "fit_result": result,
        "mix_p_weight_base": mix_p_weight_base,
        "theta2_slope_nm_per_deg": theta_slope,
        "n1_slope_nm_per_index": n1_slope,
        "n2_slope_nm_per_index": n2_slope,
        "equivalent_theta_shift_deg_for_error": equivalent_theta_shift,
        "equivalent_n1_shift_for_error": equivalent_n1_shift,
        "equivalent_n2_shift_for_error": equivalent_n2_shift,
    }
    save_json_report("single_sample_error_analysis.json", payload)

    lines = [
        "Single-sample error analysis",
        f"sample_id = {SINGLE_SAMPLE_REPORT_ID}",
        f"csv1 = {CSV_FILE_0DEG}",
        f"csv2 = {CSV_FILE_2DEG}",
        f"theta2_fit_deg = {result['theta2_fit_deg']:.6f}",
        f"d_fit_nominal_nm = {result['d_fit_nominal_calibrated_nm']:.6f}",
        f"d_fit_corrected_nm = {result['d_fit_corrected_calibrated_nm']:.6f}",
        f"best_objective = {result['best_objective']:.12e}",
        f"mix_p_weight_fit = {mix_p_weight_base:.6f}",
        f"theta2_slope_nm_per_deg = {theta_slope:.6f}",
        f"n1_slope_nm_per_index = {n1_slope:.6f}",
        f"n2_slope_nm_per_index = {n2_slope:.6f}",
    ]
    if true_thickness_nm is not None:
        lines.extend([
            f"true_thickness_nm = {true_thickness_nm:.6f}",
            f"corrected_error_nm = {corrected_error_nm:.6f}",
            f"equivalent_theta_shift_deg_for_error = {equivalent_theta_shift:.6f}" if equivalent_theta_shift is not None else "equivalent_theta_shift_deg_for_error = None",
            f"equivalent_n1_shift_for_error = {equivalent_n1_shift:.6f}" if equivalent_n1_shift is not None else "equivalent_n1_shift_for_error = None",
            f"equivalent_n2_shift_for_error = {equivalent_n2_shift:.6f}" if equivalent_n2_shift is not None else "equivalent_n2_shift_for_error = None",
        ])
    save_text_report("single_sample_error_analysis.txt", lines)

    print("=" * 90)
    print("Single-sample error analysis")
    print("=" * 90)
    print(f"theta2_fit_deg             = {result['theta2_fit_deg']:.6f}")
    print(f"d_fit_corrected_nm         = {result['d_fit_corrected_calibrated_nm']:.6f}")
    if true_thickness_nm is not None:
        print(f"true_thickness_nm          = {true_thickness_nm:.6f}")
        print(f"corrected_error_nm         = {corrected_error_nm:.6f}")
    print(f"d(theta2)/ddeg             = {theta_slope:.6f} nm/deg")
    print(f"d(d_fit)/dn1              = {n1_slope:.6f} nm/index")
    print(f"d(d_fit)/dn2              = {n2_slope:.6f} nm/index")


def run_fit_csv_compare_pols() -> None:
    global POL, FIT_MIX_WEIGHT

    original_pol = POL
    original_fit_mix_weight = FIT_MIX_WEIGHT
    results: List[Dict] = []

    try:
        for pol_name in POL_COMPARE_LIST:
            POL = str(pol_name)
            FIT_MIX_WEIGHT = (POL == "mix")
            result = fit_dual_csv_with_theta2_search_from_files(
                CSV_FILE_0DEG,
                CSV_FILE_2DEG,
                sample_id=f"{POL_COMPARE_REPORT_ID}_{pol_name}",
                save_plots=False,
            )
            result["pol_model"] = pol_name
            results.append(result)
    finally:
        POL = original_pol
        FIT_MIX_WEIGHT = original_fit_mix_weight

    rows = []
    for r in results:
        rows.append([
            r["pol_model"],
            r["theta2_fit_deg"],
            r["d_fit_nominal_nm"],
            r["d_fit_corrected_nm"],
            r["delta_d_nm"],
            r.get("mix_p_weight_fit", ""),
            r["best_objective"],
        ])

    save_rows_csv(
        "fit_csv_compare_pols.csv",
        [
            "pol_model",
            "theta2_fit_deg",
            "d_fit_nominal_nm",
            "d_fit_corrected_nm",
            "delta_d_nm",
            "mix_p_weight_fit",
            "best_objective",
        ],
        rows,
    )
    save_json_report("fit_csv_compare_pols.json", {"results": results})

    lines = [
        "Single-case polarization comparison",
        f"csv1 = {CSV_FILE_0DEG}",
        f"csv2 = {CSV_FILE_2DEG}",
        f"pol_list = {list(POL_COMPARE_LIST)}",
        "",
    ]

    for r in sorted(results, key=lambda x: x["best_objective"]):
        lines.append(
            f"{r['pol_model']}: "
            f"d_corr={r['d_fit_corrected_nm']:.6f} nm, "
            f"theta2_fit={r['theta2_fit_deg']:.6f} deg, "
            f"mix_p_weight={r.get('mix_p_weight_fit', float('nan')):.6f}, "
            f"obj={r['best_objective']:.12e}"
        )

    save_text_report("fit_csv_compare_pols.txt", lines)

    labels = [str(r["pol_model"]) for r in results]
    x = np.arange(len(labels))
    d_corr = np.array([r["d_fit_corrected_nm"] for r in results], dtype=float)
    objectives = np.array([r["best_objective"] for r in results], dtype=float)

    plt.figure(figsize=(8, 5))
    plt.bar(x, d_corr)
    plt.xticks(x, labels)
    plt.xlabel("Model polarization")
    plt.ylabel("Corrected thickness (nm)")
    plt.title("Thickness comparison across polarization models")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fit_csv_compare_pols_thickness.png", dpi=200)
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.bar(x, objectives)
    plt.xticks(x, labels)
    plt.xlabel("Model polarization")
    plt.ylabel("Best objective")
    plt.title("Objective comparison across polarization models")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "fit_csv_compare_pols_objective.png", dpi=200)
    plt.show()

    print("=" * 90)
    print("CSV fit polarization comparison")
    print("=" * 90)
    for r in sorted(results, key=lambda x: x["best_objective"]):
        print(
            f"{r['pol_model']:>3} | "
            f"d_fit_corrected = {r['d_fit_corrected_nm']:.6f} nm | "
            f"theta2_fit = {r['theta2_fit_deg']:.6f} deg | "
            f"mix_p_weight = {r.get('mix_p_weight_fit', float('nan')):.6f} | "
            f"objective = {r['best_objective']:.12e}"
        )


def run_preview_csv() -> None:
    spec = preview_csv(PREVIEW_CSV_FILE, y_selector=PREVIEW_Y_SELECTOR, save_plot=True)

    if spec.y_kind != "reflectance":
        print("\n提示：当前文件可以用于“预览”或“清洗导出”，但不能直接用于膜厚拟合。")
        print(f"当前选中的 y 列为: {spec.y_label}")
        print("如果它是 freq/THz，请把 y_selector 改到反射率列。")


def run_export_clean_csv() -> None:
    spec = export_clean_csv(
        EXPORT_CLEAN_INPUT_FILE,
        EXPORT_CLEAN_OUTPUT_FILE,
        y_selector=EXPORT_Y_SELECTOR,
    )
    print("=" * 90)
    print("Export clean csv finished")
    print("=" * 90)
    print(f"input_file   = {EXPORT_CLEAN_INPUT_FILE}")
    print(f"output_file  = {EXPORT_CLEAN_OUTPUT_FILE}")
    print(f"y_label      = {spec.y_label}")
    print(f"y_kind       = {spec.y_kind}")


def run_fit_csv() -> None:
    result = fit_dual_csv_from_files(
        CSV_FILE_0DEG,
        CSV_FILE_2DEG,
        sample_id="single_case",
        save_plots=True,
    )

    print("=" * 90)
    print("CSV fit")
    print("=" * 90)
    print(f"use_dispersion       = {result['use_dispersion']}")
    print(f"d_fit              = {result['d_fit_nm']:.6f} nm")
    print(f"d_fit_calibrated   = {result['d_fit_calibrated_nm']:.6f} nm")

    lines = [
        "CSV fit summary",
        f"csv_angle1 = {CSV_FILE_0DEG}",
        f"csv_angle2 = {CSV_FILE_2DEG}",
        f"theta_angle1 = {THETA1:.6f}",
        f"theta_angle2 = {THETA2:.6f}",
        f"use_dispersion = {result['use_dispersion']}",
        f"d_fit_nm = {result['d_fit_nm']:.6f}",
        f"d_fit_calibrated_nm = {result['d_fit_calibrated_nm']:.6f}",
    ]
    save_text_report("fit_csv_summary.txt", lines)
    save_json_report("fit_csv_summary.json", result)


def run_fit_csv_with_theta2_search() -> None:
    result = fit_dual_csv_with_theta2_search_from_files(
        CSV_FILE_0DEG,
        CSV_FILE_2DEG,
        sample_id="single_case",
        save_plots=True,
    )

    print("=" * 90)
    print("CSV fit with theta2 search")
    print("=" * 90)
    print(f"use_dispersion         = {result['use_dispersion']}")
    print(f"theta1_fixed           = {result['theta1_fixed_deg']:.6f} deg")
    print(f"theta2_nominal         = {result['theta2_nominal_deg']:.6f} deg")
    print(f"theta2_fit             = {result['theta2_fit_deg']:.6f} deg")
    print(f"d_fit_nominal          = {result['d_fit_nominal_nm']:.6f} nm")
    print(f"d_fit_corrected        = {result['d_fit_corrected_nm']:.6f} nm")
    print(f"d_fit_nominal_cal      = {result['d_fit_nominal_calibrated_nm']:.6f} nm")
    print(f"d_fit_corrected_cal    = {result['d_fit_corrected_calibrated_nm']:.6f} nm")
    print(f"delta_d                = {result['delta_d_nm']:.6f} nm")
    print(f"best_objective         = {result['best_objective']:.12e}")

    save_text_report(
        "fit_csv_with_theta2_search_summary.txt",
        [
            "CSV fit with theta2 search",
            f"csv_angle1 = {CSV_FILE_0DEG}",
            f"csv_angle2 = {CSV_FILE_2DEG}",
            f"use_dispersion = {result['use_dispersion']}",
            f"theta1_fixed_deg = {result['theta1_fixed_deg']:.6f}",
            f"theta2_nominal_deg = {result['theta2_nominal_deg']:.6f}",
            f"theta2_fit_deg = {result['theta2_fit_deg']:.6f}",
            f"d_fit_nominal_nm = {result['d_fit_nominal_nm']:.6f}",
            f"d_fit_corrected_nm = {result['d_fit_corrected_nm']:.6f}",
            f"d_fit_nominal_calibrated_nm = {result['d_fit_nominal_calibrated_nm']:.6f}",
            f"d_fit_corrected_calibrated_nm = {result['d_fit_corrected_calibrated_nm']:.6f}",
            f"delta_d_nm = {result['delta_d_nm']:.6f}",
            f"best_objective = {result['best_objective']:.12e}",
        ],
    )
    save_json_report("fit_csv_with_theta2_search_summary.json", result)
    save_rows_csv(
        "fit_csv_with_theta2_search_result.csv",
        [
            "theta1_fixed_deg",
            "theta2_nominal_deg",
            "theta2_fit_deg",
            "d_fit_nominal_nm",
            "d_fit_corrected_nm",
            "d_fit_nominal_calibrated_nm",
            "d_fit_corrected_calibrated_nm",
            "delta_d_nm",
            "best_objective",
        ],
        [[
            result["theta1_fixed_deg"],
            result["theta2_nominal_deg"],
            result["theta2_fit_deg"],
            result["d_fit_nominal_nm"],
            result["d_fit_corrected_nm"],
            result["d_fit_nominal_calibrated_nm"],
            result["d_fit_corrected_calibrated_nm"],
            result["delta_d_nm"],
            result["best_objective"],
        ]],
    )


if __name__ == "__main__":
    sync_angle_config_aliases()
    print("Running file:", __file__)
    print("RUN_MODE =", RUN_MODE)

    if RUN_MODE == "preview_csv":
        run_preview_csv()
    elif RUN_MODE == "export_clean_csv":
        run_export_clean_csv()
    elif RUN_MODE == "fit_csv":
        run_fit_csv()
    elif RUN_MODE == "fit_csv_with_theta2_search":
        run_fit_csv_with_theta2_search()
    elif RUN_MODE == "single_angle_0deg_scan":
        run_single_angle_0deg_scan()
    elif RUN_MODE == "objective_heatmap_d_theta2":
        run_objective_heatmap_d_theta2()
    elif RUN_MODE == "batch_fit_csv":
        run_batch_fit_csv()
    elif RUN_MODE == "batch_error_analysis":
        run_batch_error_analysis()
    elif RUN_MODE == "single_sample_error_analysis":
        run_single_sample_error_analysis()
    elif RUN_MODE == "fit_csv_compare_pols":
        run_fit_csv_compare_pols()
    elif RUN_MODE == "compare_80deg_at_fixed_d":
        run_compare_80deg_at_fixed_d()
    elif RUN_MODE == "theta2_scan_at_fixed_d":
        run_theta2_scan_at_fixed_d()
    else:
        raise ValueError("RUN_MODE 不正确")
