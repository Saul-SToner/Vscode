# thinfilm 函数包结构

这个目录把 `thinfilm_core.py` 中的功能按用途拆成不同模块。

目前采用兼容拆分方式：

```text
thinfilm_core.py 仍然是底层兼容引擎
thinfilm/*.py 提供更清晰的模块化调用入口
```

后续可以逐步把实现从 `thinfilm_core.py` 迁移进这些模块。

## 模块说明

```text
paths.py        数据目录和输出目录
io.py           CSV / COMSOL 表格读取
optics.py       薄膜反射率前向模型
fitting.py      厚度反演、目标函数、搜索器
diagnostics.py  误差分析、热图、批处理
reports.py      文本、JSON、CSV 输出
api.py          APP 可直接调用的高级接口
sweep.py        COMSOL 参数扫描表分析
```

## 常用调用

主线拟合：

```python
from thinfilm import fit_current_main_case

result = fit_current_main_case(save_plots=False)
print(result["d_fit_corrected_nm"])
```

自定义双角拟合：

```python
from pathlib import Path
from thinfilm import fit_two_angle

result = fit_two_angle(
    csv_angle1=Path("data/deg.s/60nm_10deg_s.csv"),
    csv_angle2=Path("data/deg.s/60nm_80deg_s.csv"),
    theta1_deg=10.0,
    theta2_deg=80.0,
    pol="s",
)
```

分析 COMSOL 参数扫描表：

```python
from thinfilm import summarize_n1b_theta_sweep

summary = summarize_n1b_theta_sweep()
```

## 给 APP 队友的建议

APP 优先调用：

```text
thinfilm.api.fit_two_angle
```

不要直接改 `thinfilm_core.py` 顶部全局变量。

`thinfilm_core.py` 目前保留给脚本运行和兼容旧流程使用。
