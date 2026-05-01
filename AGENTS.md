# 薄膜光学项目协作说明

## 1. 项目定位

本项目目前有两条并行主线：

1. 反演主线  
   从 COMSOL 或实验导出的反射率光谱中反推出单层薄膜厚度。

2. 教学仿真主树  
   依据设计报告，用 Python 复现平面多层膜系的正向仿真、导出与目录配置。

两条线共享同一个仓库，但目标不同：

- 反演主线强调“由谱线反推参数”
- 教学主树强调“给定结构正向计算 R / T / A 并组织成可演示平台”

## 2. 当前目录重点

核心文件与目录如下：

```text
thinfilm_core.py          早期集中式主脚本，仍保留大量反演入口
thinfilm/                 轻量函数包，推荐新代码从这里接入
run_teaching_demo.py      教学主树命令行入口
data/                     输入数据目录
```

`thinfilm/` 当前重点模块：

```text
thinfilm/api.py           对外高层 API
thinfilm/education.py     教学主树：多层膜正向仿真、导出、目录配置
thinfilm/sweep.py         COMSOL 扫描表分析
thinfilm/joint.py         多样本联合拟合探索
thinfilm/paths.py         数据目录与输出目录
```

## 3. 反演主线说明

### 3.1 物理模型

当前反演不是神经网络，而是物理模型反演：

1. 使用单层薄膜 Fresnel 反射模型
2. 输入两个入射角下的反射率曲线
3. 联合搜索厚度 `d`
4. 可选修正第二角 `theta2`

### 3.2 当前最稳定工程路线

```text
10° + 80°
s 偏振
双角联合反演厚度
```

推荐配置：

```python
RUN_MODE = "fit_csv_with_theta2_search"
THETA1 = 10.0
THETA2 = 80.0
POL = "s"
```

推荐输入文件：

```python
CSV_FILE_ANGLE1 = Path(r"...10deg_s.csv")
CSV_FILE_ANGLE2 = Path(r"...80deg_s.csv")
```

### 3.3 反演 API

常用调用：

```python
from thinfilm import fit_two_angle, fit_current_main_case
```

当前主线样例：

```python
result = fit_current_main_case(save_plots=False)
```

## 4. 教学主树说明

### 4.1 目标

教学主树用于复现设计报告中的平面多层膜正向仿真，包括：

1. 单层减反射膜
2. 双层减反射膜
3. 三层减反射膜
4. 高反射膜
5. 单半波型 F-P 滤光片
6. 双半波型 F-P 滤光片
7. 中性分束膜

底层方法为传输矩阵法 / 特征矩阵法，不依赖 COMSOL 即可快速生成 R / T / A 曲线。

### 4.2 命令行入口

使用：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --list
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --case single_ar
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --compare
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --catalog
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --report
```

### 4.3 教学主树 API

常用调用：

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

### 4.4 当前已具备的主树输出

1. 单案例导出
2. 第 2 章整套案例导出
3. 多曲线对比图导出
4. 主树总包导出
5. 主树目录配置导出
6. 首页卡片、分区卡片、对比图卡片统一 JSON 结构
7. 参数面板自动渲染所需表单配置

## 5. 输出位置

所有默认输出写入：

```text
C:\Users\L2791\thinfilm_outputs
```

常见输出文件包括：

```text
teaching_case_*_spectrum.csv
teaching_case_*_summary.json
teaching_case_*_summary.txt
teaching_case_*_RTA.png
teaching_case_*_main.png
teaching_compare_*.csv
teaching_compare_*.png
teaching_main_branch_catalog.json
teaching_report_case_index.csv
teaching_report_bundle_manifest.json
teaching_report_bundle_manifest.txt
```

## 6. COMSOL 数据协作约定

### 6.1 反演主线推荐导出

优先导出纯 `s` 偏振：

```text
10deg_s.csv
80deg_s.csv
```

如果要做偏振对照，再额外导出：

```text
10deg_p.csv
80deg_p.csv
```

### 6.2 mixed / avg 的处理原则

当前不建议把 COMSOL 直接导出的 `mixed` 或 `avg(0.6p)` 曲线作为主拟合输入。

更稳的方式是：

```text
分别导出纯 s 和纯 p 曲线
在 Python 后处理中按比例线性合成
```

混合模型：

```text
R_mix = eta * R_p + (1 - eta) * R_s
```

## 7. 协作建议

### 7.1 给前端 / APP 同学

优先对接这些文件或接口：

```text
thinfilm/api.py
thinfilm/education.py
C:\Users\L2791\thinfilm_outputs\teaching_main_branch_catalog.json
```

目录 JSON 已包含：

- 首页卡片
- 分区结构
- 对比图结构
- 参数表单分组
- 参数控件类型
- 默认文件路径

前端不要硬编码案例名、参数名、图路径。

### 7.2 给算法 / 建模同学

若继续反演主线，优先保持：

```text
10° + 80°
s 偏振
双角反演
```

色散、混合偏振、多厚度联合拟合可作为扩展，不要破坏主线可复现性。

## 8. 当前已知限制

1. 反演主线目前仍以单层膜模型为主
2. 尚未系统加入粗糙度、过渡层、多层反演
3. 教学主树是 Python 正向等价实现，不是 COMSOL 数值场分布复刻
4. 个别旧入口仍保留在 `thinfilm_core.py`
5. PowerShell 直接查看 JSON 时可能出现中文显示乱码，但文件本身是 UTF-8 正常内容

## 9. 推荐后续推进顺序

### 反演侧

1. 固定 `10° + 80° + s`
2. 做多厚度验证表
3. 再做小范围色散参数扫描

### 教学主树侧

1. 保持目录 JSON 结构稳定
2. 让前端先接首页、案例页、对比页
3. 再补统一结果摘要结构
4. 最后再考虑 GUI / Web 原型
