# PDRC 第一版候选摘要

本摘要记录平面多层膜 PDRC 第一版候选结果。完整批量输出位于 `~/thinfilm_outputs`。

## 结构

```text
Air / SiO2_1 / TiO2_1 / SiO2_2 / TiO2_2 / SiO2_3 / Ag / substrate
```

固定参数：

```text
d_SiO2_1 = 200 nm
d_SiO2_2 = 600 nm
d_SiO2_3 = 1.0 um
d_Ag = 500 nm
```

## 候选结果

| 版本 | d_TiO2_1 = d_TiO2_2 | 总介质厚度 | A_solar_avg | A_solar_weighted | epsilon_8_13_avg | cooling_score_weighted |
| --- | --- | --- | --- | --- | --- | --- |
| 平衡版 | 340 nm | 2.48 um | 0.0327 | 0.0454 | 0.7220 | 0.6766 |
| 高性能版 | 440 nm | 2.68 um | 0.0355 | 0.0524 | 0.7369 | 0.6845 |

## 判断

两个候选都满足：

```text
A_solar_avg < 0.15
A_solar_weighted < 0.15
epsilon_8_13_avg > 0.70
```

短波紫外端 `0.32 um` 附近存在局部吸收峰。当前已加入 `blackbody_5778K` 太阳光谱近似权重，加权后两个候选仍满足低太阳吸收要求。后续可用 ASTM G173 / AM1.5 标准光谱 CSV 替换当前近似权重。

## 复现命令

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates \
  --prefix pdrc_candidates \
  --ir-csv "path/to/ir_part1.csv" \
  --ir-csv "path/to/ir_part2.csv" \
  --solar-csv "path/to/solar_candidates.csv"
```
