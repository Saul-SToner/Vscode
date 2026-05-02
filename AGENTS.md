# 仓库协作说明

本文件是协作摘要版，完整项目说明请以：

[README.md](C:\Users\L2791\Downloads\Vscode\README.md)

为准。

## 1. 项目主线

当前仓库包含三条工作线：

1. 反演主线  
   从 COMSOL 或实验导出的光谱中反推单层薄膜厚度。

2. 教学仿真主树  
   用 Python 复现设计报告中的平面多层膜正向仿真。

3. 光栅波导研究支线  
   研究周期光栅、波导共振与窄线宽反射镜设计。

## 2. 平台边界

当前统一约定：

```text
教学平台只展示教学主树
不暴露厚度反演入口
反演代码继续保留在仓库中
```

## 3. 目录重点

```text
thinfilm_core.py
thinfilm/
guided_grating/
run_teaching_demo.py
run_guided_grating_demo.py
archive/inversion_examples/
data/
```

## 4. 当前最稳主线

若继续做厚度反演，优先保持：

```text
10° + 80°
s 偏振
双角联合反演
```

## 5. 前端对接

前端或 APP 同学优先对接：

```text
thinfilm/api.py
C:\Users\L2791\thinfilm_outputs\teaching_main_branch_catalog.json
```

不要把厚度反演入口放进教学平台首页或主菜单。

## 6. 光栅波导支线

当前支线已支持：

1. COMSOL 单谱读取
2. COMSOL 联合扫描读取
3. 自动筛选最接近目标波长的参数点

例如：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --sweep-csv "C:\path\to\2d.csv" --target-wavelength 1550
```

如果第二列不是 `period`，可显式指定参数名：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --sweep-csv "C:\path\to\5new.csv" --sweep-name t_wg --target-wavelength 1550
```

## 7. 输出目录

默认输出位置：

```text
C:\Users\L2791\thinfilm_outputs
```

## 8. 说明

如果 `PowerShell` 里中文显示乱码，通常是终端编码问题，不代表文件损坏。仓库内的 `README.md` 和 `AGENTS.md` 应视为 UTF-8 正常内容。
