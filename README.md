# 薄膜光学 Python 平台

本项目用于两类任务：

1. 薄膜反射谱反演  
   从 COMSOL 或实验导出的反射率曲线中反推出单层薄膜厚度。

2. 教学型正向仿真  
   用 Python 复现设计报告中的多层膜系案例，输出反射率、透射率、吸收率及图表。

## 当前状态

目前项目已经形成两条主线：

- 反演主线：`10° + 80° + s 偏振` 双角厚度反演
- 教学主树：第 2 章 7 个案例的正向仿真、导出和目录配置

## 项目结构

```text
thinfilm_core.py          早期集中式反演脚本
thinfilm/                 推荐使用的轻量函数包
run_teaching_demo.py      教学主树演示脚本
data/                     数据目录
```

`thinfilm/` 中常用模块：

```text
thinfilm/api.py
thinfilm/education.py
thinfilm/sweep.py
thinfilm/joint.py
thinfilm/paths.py
```

## 快速开始

### 1. 列出教学案例

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --list
```

### 2. 导出单个教学案例

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --case single_ar
```

### 3. 导出对比图

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --compare
```

### 4. 导出主树目录配置

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --catalog
```

### 5. 导出主树完整报告包

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --report
```

## 教学主树覆盖案例

1. 单层减反射膜
2. 双层减反射膜
3. 三层减反射膜
4. 高反射膜
5. 单半波型 F-P 滤光片
6. 双半波型 F-P 滤光片
7. 中性分束膜

## 常用 Python API

### 反演主线

```python
from thinfilm import fit_two_angle, fit_current_main_case

result = fit_current_main_case(save_plots=False)
```

### 教学主树

```python
from thinfilm import (
    list_teaching_cases,
    simulate_teaching_case,
    export_teaching_case_outputs,
    export_teaching_comparison_figures,
    export_teaching_main_branch_catalog,
    export_teaching_report_bundle,
)
```

## 主要输出

所有默认输出写到：

```text
C:\Users\L2791\thinfilm_outputs
```

重要文件：

```text
teaching_main_branch_catalog.json
teaching_report_case_index.csv
teaching_report_bundle_manifest.json
teaching_report_bundle_manifest.txt
teaching_case_*_main.png
teaching_compare_*.png
```

## 目录配置说明

`teaching_main_branch_catalog.json` 当前已经包含：

- 首页卡片 `home_cards`
- 首页摘要 `home_summary`
- 分区结构 `sections`
- 对比图结构 `comparisons`
- 对比图分组 `comparison_groups`
- 参数控件定义 `case_controls`
- 参数表单分组 `case_form_groups`
- 表单渲染提示 `form_ui_meta`

这份 JSON 可以直接提供给前端或 APP 原型使用。

## 反演主线说明

当前最稳定路线是：

```text
10° + 80°
s 偏振
双角联合厚度反演
```

推荐输入：

```text
10deg_s.csv
80deg_s.csv
```

## 注意事项

1. 当前反演主线主要针对单层膜
2. `mixed / avg` 不建议直接作为主拟合输入
3. JSON 文件是 UTF-8，若 PowerShell 显示中文乱码，通常是终端编码问题，不是文件损坏
4. 教学主树是 Python 正向实现，适合教学平台和前端演示，不等于 COMSOL 场分布逐点复刻

## 后续建议

1. 前端优先对接 `teaching_main_branch_catalog.json`
2. 保持主树目录结构稳定
3. 继续补统一结果摘要结构
4. 再进入 GUI / Web 原型阶段
