# PDRC 被动日间辐射冷却

这里放 PDRC 平面多层膜宽波段筛选和 COMSOL 结果摘要脚本。

常用根目录入口：

```bash
python run_case.py --group pdrc --case cooling_bundle
python run_case.py --group pdrc --case cooling_bundle -- --comsol-csv "path/to/pdrc_ir_window.csv"
```

分析多段 COMSOL 参数扫描：

```bash
python run_case.py --group pdrc --case cooling_bundle -- --analyze-comsol-candidates ^
  --prefix pdrc_candidates ^
  --ir-csv "path/to/pdrc_scan_part1.csv" ^
  --ir-csv "path/to/pdrc_scan_part2.csv" ^
  --solar-csv "path/to/pdrc_candidates_solar.csv"
```

该入口会自动合并分段红外 CSV、按厚度参数去重、计算 `epsilon_8_13_avg`，并在提供太阳波段 CSV 时计算 `A_solar_avg` 和 `cooling_score`。
默认会使用 `blackbody_5778K` 作为快速近似权重；当前正式 PDRC 结果已通过 `--solar-weight-csv` 接入 ASTM G173-03 AM1.5 global tilt 光谱，额外导出 `A_solar_weighted` 和 `cooling_score_weighted`。

当前建议先验证：

```text
太阳波段：0.3-2.5 um 低吸收
红外窗口：8-13 um 高发射
```

当前真实材料验证主候选：

```text
结构：
Air / SiO2_1 / TiO2_1 / SiO2_2 / TiO2_2 / SiO2_3 / Ag / substrate

d_SiO2_1 = 200 nm
d_TiO2_1 = 440 nm
d_SiO2_2 = 500 nm
d_TiO2_2 = 440 nm
d_SiO2_3 = 1000 nm
d_Ag = 500 nm

A_solar_avg = 0.0466
A_solar_weighted(ASTM G173) = 0.0435
R_solar_weighted(ASTM G173) = 0.9565
epsilon_8_13_avg = 0.8044
cooling_score_weighted(ASTM G173) = 0.7609
```

该候选满足 `A_solar_avg < 0.15`、`A_solar_weighted < 0.15`、`R_solar_weighted > 0.90` 和 `epsilon_8_13_avg > 0.70`。当前标准太阳加权使用 ASTM G173-03 AM1.5 global tilt 光谱文件。

最新有效数据：

```text
pdrc_real_materials_solar_valid.csv
pdrc_real_materials_ir_valid.csv
```

对应处理输出位于：

```text
C:\Users\L2791\thinfilm_outputs\pdrc_real_materials_solar_valid_spectrum.png
C:\Users\L2791\thinfilm_outputs\pdrc_real_materials_solar_valid_metrics.png
C:\Users\L2791\thinfilm_outputs\pdrc_real_materials_ir_valid_spectrum.png
```

保留对照候选：

```text
红外最高对照：d_SiO2_1 = 240 nm, d_SiO2_2 = 600 nm
epsilon_8_13_avg = 0.8011
```

专题说明页：

```text
pdrc_multilayer_cooling/
```
