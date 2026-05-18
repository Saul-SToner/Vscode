# ASTM G173-03 AM1.5 标准太阳光谱

本目录保存 PDRC 模块使用的标准太阳光谱权重。

## 数据来源

数据来自 NREL/NLR 的 Reference Air Mass 1.5 Spectra 页面，对应 ASTM G173-03 Reference Spectra。页面说明该表给出 wavelength、extraterrestrial spectral irradiance、direct normal spectral irradiance 和 global total spectral irradiance。

项目中使用：

```text
Global tilt W*m-2*nm-1
```

作为 AM1.5G / 37 degree tilted surface 的太阳光谱权重。

## 文件

```text
ASTMG173.csv
```

NREL/NLR 下载的原始 CSV。

```text
astm_g173_am15_global_tilt.csv
```

项目整理后的权重文件，列为：

```csv
lambda_um,irradiance,source
```

## PDRC 使用方式

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates \
  --prefix pdrc_scan_sio2_1_2_astm_g173_final \
  --parameter-selector d_SiO2_1,d_SiO2_2 \
  --parameter-label d_SiO2_1_nm,d_SiO2_2_nm \
  --ir-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_coarse_ir.csv" \
  --solar-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_coarse_solar_candidates.csv" \
  --solar-weight-csv "data/real_spectrum/astm_g173_am15/astm_g173_am15_global_tilt.csv"
```

当前主候选 `d_SiO2_1=200 nm, d_SiO2_2=500 nm` 的 ASTM G173 加权结果：

```text
A_solar_weighted = 0.0306
epsilon_8_13_avg = 0.8004
cooling_score_weighted = 0.7698
```
