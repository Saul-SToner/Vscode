# 真实材料库统一接入

## 1. 模块定位

该模块统一读取 `data/real_nk/` 下的真实材料光学常数，并为教学 TMM、PDRC、Tamm 等模块提供统一的 `n(lambda), k(lambda)` 插值入口。

## 2. 当前材料

首批材料包括：

- SiO2: Malitson 1965; Tan 1998
- TiO2: Devore 1951 ordinary ray
- MgF2: Dodge 1984 ordinary ray
- Al2O3: Malitson 1962 ordinary ray
- Au: Johnson and Christy 1972
- Ag: Johnson and Christy 1972
- Si: Aspnes and Studna 1983

## 3. Python 入口

```bash
python run_material_library_demo.py
```

该命令会导出：

- 真实材料库目录表
- 常用波长采样表
- 材料覆盖范围图
- 常数折射率 TMM 与真实色散 TMM 对比案例

## 4. API 入口

```python
from thinfilm import (
    list_real_materials,
    material_nk_at,
    simulate_teaching_design_real_materials,
)
```

## 5. 使用边界

真实材料只能在数据源覆盖范围内使用。当前 TiO2 Devore 数据覆盖 `0.43-1.53 um`，Johnson-Christy Au/Ag 覆盖到约 `1.94 um`，因此不能直接外推到 `8-13 um` PDRC 或 `4-5 um` Tamm 中红外模块。中红外模块应优先使用 COMSOL 材料库或补充中红外光学常数数据。
