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
d_TiO2_1 = 80 nm
d_SiO2_2 = 600 nm
d_TiO2_2 = 80 nm
d_SiO2_3 = 1.0 um
d_Ag = 500 nm
```

下一步优先扫描：

```text
d_SiO2_2 = range(300[nm], 50[nm], 1200[nm])
lam = range(8[um], 0.1[um], 13[um])
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
pdrc_scan_dSiO2_2_ir.csv
```

## 5. Python 运行方式

```bash
python run_pdrc_cooling_bundle.py
python run_pdrc_cooling_bundle.py --comsol-csv "path/to/pdrc_ir.csv"
```

## 6. 结果判断

第一版成功标准可以设为 `A_solar_avg < 0.15` 且 `epsilon_8_13_avg > 0.70`。如果红外平均发射率不足，优先扫描 SiO2 和 TiO2 层厚。

当前已知趋势：

```text
d_SiO2_1 单参数细扫最佳约在 200 nm
epsilon_8_13_avg 约为 0.684
主要短板是 8.9 um 附近存在低谷
```

因此继续单独细扫 `d_SiO2_1` 收益不大，下一步更应扫描 `d_SiO2_2` 或 TiO2 层厚来抬高 `8-10 um` 区间。

## 7. data 与 outputs 约定

`data/` 用于放小型示例或说明文件，不建议把大型 COMSOL 扫描 CSV 长期提交到仓库。

`outputs/` 只放展示级小图或摘要说明；完整运行输出默认放在：

```text
~/thinfilm_outputs
```
