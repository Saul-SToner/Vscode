# PDRC 被动日间辐射冷却薄膜

## 1. 物理对象

平面多层膜 PDRC 结构，目标是在太阳波段低吸收，在 8-13 um 大气窗口高发射。

## 2. 推荐比较量

- `R(lambda)`
- `T(lambda)`
- `A(lambda)`
- `emissivity(lambda) ~= A(lambda)`
- `A_solar_avg`
- `epsilon_8_13_avg`
- `cooling_score`

## 3. COMSOL 导出要求

太阳波段建议导出 `0.3-2.5 um`，红外窗口建议导出 `8-13 um`：

- `lambda`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`
- `1-abs(ewfd.S11)^2-abs(ewfd.S21)^2`

## 4. Python 运行方式

```bash
python run_pdrc_cooling_bundle.py
```

## 5. 结果判断

第一版成功标准可以设为 `A_solar_avg < 0.15` 且 `epsilon_8_13_avg > 0.70`。如果红外平均发射率不足，优先扫描 SiO2 和 TiO2 层厚。
