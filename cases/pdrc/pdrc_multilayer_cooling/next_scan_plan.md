# PDRC 下一轮微调扫描方案

## 1. 当前基准

当前 PDRC 平面多层膜已经有两个可展示候选：

```text
平衡候选：
d_TiO2_1 = d_TiO2_2 = 340 nm
d_SiO2_1 = 200 nm
d_SiO2_2 = 600 nm
d_SiO2_3 = 1000 nm

高发射候选：
d_TiO2_1 = d_TiO2_2 = 440 nm
d_SiO2_1 = 200 nm
d_SiO2_2 = 600 nm
d_SiO2_3 = 1000 nm
```

两者都已经满足：

```text
A_solar_weighted < 0.15
epsilon_8_13_avg > 0.70
```

下一步不是继续盲目扩大 `d_TiO2`，而是在候选点附近微调 SiO2 层，让红外窗口发射率更高，同时保持太阳波段吸收较低。

## 2. 第一轮推荐扫描

优先扫描高发射候选附近：

```text
d_TiO2_1 = d_TiO2_2 = 440[nm]
d_Ag = 500[nm]

d_SiO2_1 = range(160[nm], 20[nm], 260[nm])
d_SiO2_2 = range(500[nm], 50[nm], 750[nm])
d_SiO2_3 = 1000[nm]
```

红外波长：

```text
lam = range(8[um], 0.1[um], 13[um])
```

这组是二维微调，参数量适中：

```text
6 个 d_SiO2_1 点
6 个 d_SiO2_2 点
51 个波长点
总计算约 1836 个频点
```

如果 COMSOL 计算较慢，可以先把步长放粗：

```text
d_SiO2_1 = range(160[nm], 40[nm], 280[nm])
d_SiO2_2 = range(500[nm], 100[nm], 800[nm])
lam = range(8[um], 0.2[um], 13[um])
```

## 3. 第二轮推荐扫描

如果第一轮最优点贴近扫描边界，再以最优点为中心做细扫：

```text
d_SiO2_1 = range(best_d_SiO2_1 - 30[nm], 10[nm], best_d_SiO2_1 + 30[nm])
d_SiO2_2 = range(best_d_SiO2_2 - 75[nm], 25[nm], best_d_SiO2_2 + 75[nm])
lam = range(8[um], 0.1[um], 13[um])
```

## 4. 太阳波段复核

红外筛出前 3 到 5 个候选后，再单独跑太阳波段：

```text
lam = range(0.3[um], 0.02[um], 2.5[um])
```

不要对所有二维点都跑太阳波段。先用红外窗口筛掉大部分点，再对候选点算太阳吸收，效率更高。

## 5. COMSOL 导出列

红外和太阳波段都导出相同表达式：

```text
lam
d_SiO2_1
d_SiO2_2
abs(ewfd.S11)^2
abs(ewfd.S21)^2
1-abs(ewfd.S11)^2-abs(ewfd.S21)^2
```

如果你只扫一个 SiO2 参数，也可以只导出对应参数列。

## 6. Python 分析命令

二维红外扫描：

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates ^
  --prefix pdrc_scan_sio2_1_2_ir ^
  --parameter-selector d_SiO2_1,d_SiO2_2 ^
  --parameter-label d_SiO2_1_nm,d_SiO2_2_nm ^
  --ir-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_ir.csv"
```

如果后续导出了候选点太阳波段：

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates ^
  --prefix pdrc_scan_sio2_1_2_final ^
  --parameter-selector d_SiO2_1,d_SiO2_2 ^
  --parameter-label d_SiO2_1_nm,d_SiO2_2_nm ^
  --ir-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_ir.csv" ^
  --solar-csv "C:\Users\L2791\OneDrive\Desktop\deg.p\pdrc_scan_sio2_1_2_solar_candidates.csv"
```

## 7. 判断标准

优先选择：

```text
epsilon_8_13_avg 更高
A_solar_weighted < 0.15
total_dielectric_thickness 不明显增加
```

建议展示时保留两个版本：

```text
薄膜厚度受限版：总介质厚度更小
高发射性能版：epsilon_8_13_avg 更高
```
