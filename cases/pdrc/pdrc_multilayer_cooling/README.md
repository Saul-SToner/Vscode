# 基于多层薄膜光谱选择性的被动日间辐射冷却结构

## 1. 物理对象

平面多层膜 PDRC 结构，目标是在太阳波段低吸收，在 `8-13 um` 大气窗口高发射。对不透明金属背反射结构，可近似使用 Kirchhoff 定律：

```text
emissivity(lambda) ~= absorptivity(lambda) = A(lambda)
```

因此该模块的核心是把光谱选择性写成可量化指标，而不是只看单张曲线。

## 2. 结构参数

第一版平面结构：

```text
Air / SiO2_1 / TiO2_1 / SiO2_2 / TiO2_2 / SiO2_3 / Ag / substrate
```

当前建议基准参数：

```text
d_SiO2_1 = 200 nm  # 红外细扫当前最佳附近
d_SiO2_2 = 600 nm
d_SiO2_3 = 1.0 um
d_Ag = 500 nm
```

第一版保留两个候选：

```text
平衡版：
d_TiO2_1 = d_TiO2_2 = 340 nm
total_dielectric_thickness = 2.48 um

高性能版：
d_TiO2_1 = d_TiO2_2 = 440 nm
total_dielectric_thickness = 2.68 um
```

## 3. 推荐比较量

- `R(lambda)`
- `T(lambda)`
- `A(lambda)`
- `emissivity(lambda) ~= A(lambda)`
- `A_solar_avg`
- `epsilon_8_13_avg`
- `cooling_score`

## 4. COMSOL 导出要求

太阳波段建议导出 `0.3-2.5 um`，红外窗口建议导出 `8-13 um`：

- `lambda`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`
- `1-abs(ewfd.S11)^2-abs(ewfd.S21)^2`

建议文件命名：

```text
pdrc_real_materials_solar_0p3_2p5.csv
pdrc_real_materials_ir_8_13.csv
pdrc_scan_dTiO2_equal_ir_40_440_full_summary.csv
pdrc_candidates_340_440_final_metrics.csv
```

## 5. Python 运行方式

```bash
python run_pdrc_cooling_bundle.py
python run_pdrc_cooling_bundle.py --comsol-csv "path/to/pdrc_ir.csv"
```

候选扫描分析：

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates \
  --prefix pdrc_candidates \
  --ir-csv "path/to/ir_part1.csv" \
  --ir-csv "path/to/ir_part2.csv" \
  --solar-csv "path/to/solar_candidates.csv"
```

默认太阳光谱加权：

```bash
--solar-weight-mode blackbody_5778K
```

如果已有 ASTM G173 / AM1.5 光谱 CSV，可替换为：

```bash
--solar-weight-csv "path/to/solar_spectrum.csv"
```

对应 Python API：

```python
from thinfilm import export_pdrc_comsol_candidates

export_pdrc_comsol_candidates(
    ir_csv_files=["path/to/ir_part1.csv", "path/to/ir_part2.csv"],
    solar_csv_file="path/to/solar_candidates.csv",
    prefix="pdrc_candidates",
)
```

多参数联合扫描也可以直接读，例如同时扫描 `d_SiO2_1` 和 `d_SiO2_2`：

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates \
  --prefix pdrc_scan_sio2_1_2_final \
  --parameter-selector d_SiO2_1,d_SiO2_2 \
  --parameter-label d_SiO2_1_nm,d_SiO2_2_nm \
  --ir-csv "path/to/pdrc_scan_sio2_1_2_ir.csv" \
  --solar-csv "path/to/pdrc_scan_sio2_1_2_solar_candidates.csv"
```

下一轮 COMSOL 扫描建议见：

```text
cases/pdrc/pdrc_multilayer_cooling/next_scan_plan.md
```

## 6. 结果判断

第一版成功标准可以设为 `A_solar_avg < 0.15` 且 `epsilon_8_13_avg > 0.70`。如果红外平均发射率不足，优先扫描 SiO2 和 TiO2 层厚。

第一版候选结果：

```text
平衡版：d_TiO2 = 340 nm
A_solar_avg = 0.0327
A_solar_weighted = 0.0454
R_solar_avg = 0.9673
epsilon_8_13_avg = 0.7220
cooling_score_weighted = 0.6766

高性能版：d_TiO2 = 440 nm
A_solar_avg = 0.0355
A_solar_weighted = 0.0524
R_solar_avg = 0.9645
epsilon_8_13_avg = 0.7369
cooling_score_weighted = 0.6845
```

两者都满足 `A_solar_avg < 0.15`、`A_solar_weighted < 0.15` 和 `epsilon_8_13_avg > 0.70`。需要说明的是，太阳波段短波端 `0.32 um` 附近存在局部吸收峰，但加权平均太阳吸收仍然较低；后续可用 ASTM G173 / AM1.5 标准光谱替换当前 `blackbody_5778K` 近似权重。

## 7. data 与 outputs 约定

`data/` 用于放小型示例或说明文件，不建议把大型 COMSOL 扫描 CSV 长期提交到仓库。

`outputs/` 只放展示级小图或摘要说明；完整运行输出默认放在：

```text
~/thinfilm_outputs
```
