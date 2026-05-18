# PDRC 平面多层膜最终候选摘要

本摘要记录平面多层膜 PDRC 真实材料宽波段验证结果。完整批量输出位于 `~/thinfilm_outputs`。

## 结构

```text
Air / SiO2_1 / TiO2_1 / SiO2_2 / TiO2_2 / SiO2_3 / Ag / substrate
```

主候选参数：

```text
d_SiO2_1 = 200 nm
d_TiO2_1 = 440 nm
d_SiO2_2 = 500 nm
d_TiO2_2 = 440 nm
d_SiO2_3 = 1.0 um
d_Ag = 500 nm
```

## 候选结果

| 版本 | d_SiO2_1 | d_SiO2_2 | d_TiO2_1 = d_TiO2_2 | A_solar_avg | A_solar_weighted | epsilon_8_13_avg | cooling_score_weighted |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 真实材料验证主候选 | 200 nm | 500 nm | 440 nm | 0.0466 | 0.0435 | 0.8044 | 0.7609 |
| 历史扫描红外最高对照 | 240 nm | 600 nm | 440 nm | 0.0401 | 0.0389 | 0.8011 | 0.7621 |

表中的 `A_solar_weighted` 使用 ASTM G173-03 AM1.5 global tilt 光谱。展示主线采用最新 `pdrc_real_materials_solar_valid.csv` 与 `pdrc_real_materials_ir_valid.csv`；历史扫描红外最高对照只用于说明早期筛选过程，不作为最终验证口径。

## 判断

主候选满足：

```text
A_solar_avg < 0.15
A_solar_weighted < 0.15
epsilon_8_13_avg > 0.70
```

短波紫外端 `0.32 um` 附近存在局部吸收峰。当前已加入 ASTM G173-03 AM1.5 global tilt 标准太阳光谱权重，加权后主候选仍满足低太阳吸收要求。

## 已用数据

```text
红外粗扫：
C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_coarse_ir.csv

太阳候选：
C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_coarse_solar_candidates.csv

最终太阳波段验证：
C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_real_materials_solar_valid.csv

最终红外窗口验证：
C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_real_materials_ir_valid.csv
```

主要输出位于：

```text
C:\Users\L2791\thinfilm_outputs\pdrc_scan_sio2_1_2_coarse_final_final_metrics.csv
C:\Users\L2791\thinfilm_outputs\pdrc_scan_sio2_1_2_coarse_final_final_metrics.png
C:\Users\L2791\thinfilm_outputs\pdrc_scan_sio2_1_2_coarse_final_ir_summary.png
C:\Users\L2791\thinfilm_outputs\pdrc_scan_sio2_1_2_astm_g173_final_final_metrics.csv
C:\Users\L2791\thinfilm_outputs\pdrc_scan_sio2_1_2_astm_g173_final_final_metrics.png
C:\Users\L2791\thinfilm_outputs\pdrc_pretty_astm_g173_final_dashboard.png
C:\Users\L2791\thinfilm_outputs\pdrc_pretty_astm_g173_final_metrics.png
C:\Users\L2791\thinfilm_outputs\pdrc_pretty_astm_g173_ir_summary.png
C:\Users\L2791\thinfilm_outputs\pdrc_real_materials_solar_valid_spectrum.png
C:\Users\L2791\thinfilm_outputs\pdrc_real_materials_solar_valid_metrics.png
C:\Users\L2791\thinfilm_outputs\pdrc_real_materials_ir_valid_spectrum.png
```

展示优先级：

```text
1. pdrc_real_materials_solar_valid_spectrum.png
   用于展示最终主候选在 0.3-2.5 um 太阳波段的 R/T/A 光谱。

2. pdrc_real_materials_ir_valid_spectrum.png
   用于展示最终主候选在 8-13 um 大气窗口的高发射。

3. pdrc_real_materials_solar_valid_metrics.png
   用于展示 ASTM G173 加权太阳吸收、太阳反射和最终 cooling score。
```

## 复现命令

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates \
  --prefix pdrc_scan_sio2_1_2_astm_g173_final \
  --parameter-selector d_SiO2_1,d_SiO2_2 \
  --parameter-label d_SiO2_1_nm,d_SiO2_2_nm \
  --ir-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_coarse_ir.csv" \
  --solar-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_coarse_solar_candidates.csv" \
  --solar-weight-csv "C:\Users\L2791\Downloads\Vscode\data\real_spectrum\astm_g173_am15\astm_g173_am15_global_tilt.csv"
```
