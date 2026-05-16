# PDRC 被动日间辐射冷却

这里放 PDRC 平面多层膜宽波段筛选和 COMSOL 结果摘要脚本。

常用根目录入口：

```bash
python run_pdrc_cooling_bundle.py
python run_pdrc_cooling_bundle.py --comsol-csv "path/to/pdrc_ir_window.csv"
```

分析多段 COMSOL 参数扫描：

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates ^
  --prefix pdrc_candidates ^
  --ir-csv "path/to/pdrc_scan_part1.csv" ^
  --ir-csv "path/to/pdrc_scan_part2.csv" ^
  --solar-csv "path/to/pdrc_candidates_solar.csv"
```

该入口会自动合并分段红外 CSV、按厚度参数去重、计算 `epsilon_8_13_avg`，并在提供太阳波段 CSV 时计算 `A_solar_avg` 和 `cooling_score`。
默认还会使用 `blackbody_5778K` 作为太阳光谱近似权重，额外导出 `A_solar_weighted` 和 `cooling_score_weighted`。如果后续有 ASTM G173 / AM1.5 光谱 CSV，可通过 `--solar-weight-csv` 替换。

当前建议先验证：

```text
太阳波段：0.3-2.5 um 低吸收
红外窗口：8-13 um 高发射
```

当前第一版候选：

```text
平衡版：d_TiO2_1 = d_TiO2_2 = 340 nm
高性能版：d_TiO2_1 = d_TiO2_2 = 440 nm
```

两者都满足 `A_solar_avg < 0.15` 和 `epsilon_8_13_avg > 0.70`。
按 `blackbody_5778K` 加权后也满足 `A_solar_weighted < 0.15`。

专题说明页：

```text
pdrc_multilayer_cooling/
```
