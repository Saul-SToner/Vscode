# 薄膜光学 Python 平台

本仓库用于支撑三条相关但目标不同的工作线：

1. 反演主线  
   从 COMSOL 或实验导出的反射率光谱中，反推出单层薄膜厚度与部分相关参数。

2. 教学仿真主树  
   依据设计报告，用 Python 复现平面多层膜的正向仿真、结果导出与前端目录配置。

3. 光栅波导研究支线  
   从异构薄膜出发，延伸到周期光栅、波导共振与窄线宽反射镜设计。

---

## 1. 当前约定

当前仓库的对外展示边界如下：

```text
教学平台只展示教学主树
不暴露厚度反演入口
反演代码继续保留在仓库中
```

也就是说：

- 教学平台面向“正向仿真与演示”
- 厚度反演保留给研究模式、内部工具和后续扩展

---

## 2. 目录结构

核心目录与文件：

```text
thinfilm_core.py             早期集中式脚本，保留大量反演入口
thinfilm/                    当前推荐使用的轻量函数包
guided_grating/              光栅波导研究支线
run_teaching_demo.py         教学主树命令行入口
run_guided_grating_demo.py   光栅波导支线命令行入口
archive/inversion_examples/  归档后的反演样本目录
data/                        主路径说明目录，不再存放反演样本
```

`thinfilm/` 当前重点模块：

```text
thinfilm/api.py
thinfilm/education.py
thinfilm/sweep.py
thinfilm/joint.py
thinfilm/paths.py
```

---

## 3. 教学主树

### 3.1 目标

教学主树用于复现设计报告中的平面多层膜正向仿真，当前覆盖：

1. 单层减反射膜
2. 双层减反射膜
3. 三层减反射膜
4. 高反射膜
5. 单半波型 F-P 滤光片
6. 双半波型 F-P 滤光片
7. 中性分束膜

底层方法为传输矩阵法 / 特征矩阵法，不依赖 COMSOL 即可快速生成 `R / T / A` 曲线。

### 3.2 命令行入口

列出教学案例：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --list
```

导出单个案例：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --case single_ar
```

导出对比图：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --compare
```

导出目录配置：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --catalog
```

导出完整报告包：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_teaching_demo.py --report
```

### 3.3 常用 API

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

### 3.4 当前已具备的输出

1. 单案例导出
2. 第 2 章整套案例导出
3. 多曲线对比图导出
4. 主树总包导出
5. 主树目录配置导出
6. 首页卡片、分区卡片、对比图卡片统一 JSON 结构
7. 参数面板自动渲染所需表单配置

### 3.5 前端对接约定

优先对接：

```text
thinfilm/api.py
thinfilm/education.py
C:\Users\L2791\thinfilm_outputs\teaching_main_branch_catalog.json
```

`teaching_main_branch_catalog.json` 当前已包含：

- `home_cards`
- `home_summary`
- `sections`
- `comparisons`
- `comparison_groups`
- `case_controls`
- `case_form_groups`
- `form_ui_meta`
- `default_files`
- `platform_scope`

其中平台边界已写入：

```text
show_thickness_inversion = false
```

前端不要硬编码案例名、参数名、图路径。

---

## 4. 反演主线

### 4.1 物理模型

当前反演不是神经网络，而是物理模型反演：

1. 使用单层薄膜 Fresnel 反射模型
2. 输入两个入射角下的反射率曲线
3. 联合搜索厚度 `d`
4. 可选修正第二角 `theta2`

### 4.2 当前最稳定工程路线

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

推荐输入：

```python
CSV_FILE_ANGLE1 = Path(r"...10deg_s.csv")
CSV_FILE_ANGLE2 = Path(r"...80deg_s.csv")
```

### 4.3 常用 API

```python
from thinfilm import fit_two_angle, fit_current_main_case

result = fit_current_main_case(save_plots=False)
```

### 4.4 COMSOL 数据建议

优先导出纯 `s` 偏振：

```text
10deg_s.csv
80deg_s.csv
```

若做偏振对照，再额外导出：

```text
10deg_p.csv
80deg_p.csv
```

当前不建议把 COMSOL 直接导出的 `mixed` 或 `avg(0.6p)` 作为主拟合输入。更稳的方式是：

```text
分别导出纯 s 和纯 p
在 Python 后处理中按比例线性合成
```

混合模型：

```text
R_mix = eta * R_p + (1 - eta) * R_s
```

---

## 5. 光栅波导支线

### 5.1 路线定位

该支线用于承接：

```text
异构薄膜
-> 周期光栅
-> 波导共振
-> 窄线宽反射镜设计
```

当前状态：

1. 已建立独立包结构
2. 已定义最小参数模型
3. 已接入谱线摘要与导出
4. 已提供 `run_guided_grating_demo.py`
5. 已支持 COMSOL 单谱和联合扫描表读取

### 5.2 入口脚本

运行最小占位示例：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py
```

读取 COMSOL 单条光谱：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --csv "C:\path\to\Grant.csv"
```

读取 `lambda + period` 联合扫描：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --sweep-csv "C:\path\to\2d.csv" --target-wavelength 1550
```

读取 `lambda + t_wg` 联合扫描：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --sweep-csv "C:\path\to\5new.csv" --sweep-name t_wg --target-wavelength 1550
```

### 5.3 当前分析能力

当前联合扫描模式会自动：

1. 按第二参数分组
2. 提取各组峰位、峰值反射率、FWHM
3. 按目标波长误差排序
4. 给出最佳候选参数
5. 同时导出整张扫描表摘要和最佳曲线

### 5.4 当前阶段性结论

截至当前，支线已经验证到：

- `period` 是强主控参数
- 已可把窄带高反峰调到 `1550 nm` 附近
- `period = 980.0 nm` 时已有接近目标波长的设计点

但这条支线仍有提升空间，例如：

- 峰位进一步精确锁定
- `t_wg / fill_factor / t_grating` 的系统影响
- 吸收和损耗影响
- 模态机理解释

---

## 6. 输出目录

所有默认输出写入：

```text
C:\Users\L2791\thinfilm_outputs
```

常见输出包括：

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
guided_grating_*_summary.json
guided_grating_*_summary.txt
guided_grating_*_main.png
guided_grating_*_period_summary.csv
```

---

## 7. 协作说明

这一部分同时替代原来的 `AGENTS` 核心内容，后续请以本文件为准。

### 7.1 给前端 / APP 同学

优先接教学主树，不接厚度反演入口。

推荐使用：

```text
thinfilm/api.py
C:\Users\L2791\thinfilm_outputs\teaching_main_branch_catalog.json
```

### 7.2 给算法 / 建模同学

若继续反演主线，优先保持：

```text
10° + 80°
s 偏振
双角反演
```

色散、混合偏振、多厚度联合拟合可以作为扩展，但不要破坏主线可复现性。

### 7.3 给支线研究同学

当前建议的推进顺序：

1. 先锁 `period`
2. 再看 `t_wg`
3. 再看 `fill_factor`
4. 最后补吸收影响

---

## 8. 已知限制

1. 反演主线目前仍以单层膜模型为主
2. 尚未系统加入粗糙度、过渡层、多层反演
3. 教学主树是 Python 正向等价实现，不是 COMSOL 场分布逐点复刻
4. `thinfilm_core.py` 中仍保留部分旧入口
5. PowerShell 直接查看中文 JSON 或 Markdown 时，若乱码通常是终端编码问题，不是文件损坏
6. `guided_grating/solver.py` 当前仍保留占位求解器，仅用于工程骨架，不作为正式物理论证依据

---

## 9. 环境依赖

安装依赖：

```powershell
pip install -r requirements.txt
```

当前依赖文件：

```text
requirements.txt
```

缓存和输出忽略规则见：

```text
.gitignore
```

---

## 10. 推荐推进顺序

### 反演侧

1. 固定 `10° + 80° + s`
2. 做多厚度验证表
3. 再做小范围色散参数扫描

### 教学主树侧

1. 保持目录 JSON 结构稳定
2. 让前端先接首页、案例页、对比页
3. 再补统一结果摘要结构
4. 最后再考虑 GUI / Web 原型

### 光栅波导支线

1. 锁最终 `period`
2. 扫 `t_wg`
3. 扫 `fill_factor`
4. 补吸收与损耗影响
