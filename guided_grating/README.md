# 光栅波导支线

本目录用于承接如下研究支线：

```text
异构薄膜
-> 周期光栅
-> 波导共振
-> 窄线宽反射镜设计
```

当前目标不是立刻完成正式求解器，而是先把：

1. 参数结构
2. 谱线摘要
3. 导出链路
4. COMSOL 数据接入口

稳定下来。

## 当前模块

```text
guided_grating/models.py
guided_grating/comsol_io.py
guided_grating/solver.py
guided_grating/spectra.py
guided_grating/export.py
guided_grating/examples.py
```

## 当前状态

目前支线已经具备三种入口：

1. 占位最小示例
2. COMSOL 单条光谱 CSV 读取
3. COMSOL `lambda-period` 联合扫描 CSV 读取与自动筛选

其中：

- 占位最小示例用于搭建工程骨架
- COMSOL 单谱读取用于真实谱线后处理
- 联合扫描读取用于快速筛选最接近目标波长的周期

## 命令行入口

运行占位最小示例：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py
```

读取 COMSOL 导出的单条光谱 CSV：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --csv "C:\path\to\Grant.csv"
```

读取 COMSOL 导出的 `lambda-period` 联合扫描表，并按目标波长自动筛选：

```powershell
C:/Users/L2791/AppData/Local/Programs/Python/Python313/python.exe .\run_guided_grating_demo.py --sweep-csv "C:\path\to\2d.csv" --target-wavelength 1550
```

## 当前支持的 COMSOL 表格类型

### 1. 单条光谱表

典型列结构：

```text
lambda0 (m)
总反射率
总透射率
吸收率
总反射率和透射率
```

即使数值列是 COMSOL 导出的“数值 + 相位”格式，也会自动提取前面的实数部分。

### 2. 联合扫描表

典型列结构：

```text
lambda0 (m)
period (m)
总反射率
总透射率
吸收率
总反射率和透射率
```

读取后会自动：

1. 按 `period` 分组
2. 逐组提取峰值反射率、峰位、线宽
3. 按目标波长误差排序
4. 给出最佳候选周期

## 输出内容

读取或生成谱线后，会默认导出到：

```text
C:\Users\L2791\thinfilm_outputs
```

常见输出包括：

```text
*_spectrum.csv
*_summary.json
*_summary.txt
*_RTA.png
*_main.png
*_period_summary.csv
```

其中联合扫描模式会额外输出：

- 整张扫描表的周期摘要
- 最佳周期对应的单条谱线图与摘要

## 重要说明

### 1. 占位求解器说明

`solver.py` 里的默认求解器当前仍是：

```text
placeholder surrogate
```

它只用于：

- 支线工程骨架
- 导出链路验证
- 接口预留

不应用于正式物理论证。

### 2. COMSOL 数据说明

如果通过 `--csv` 或 `--sweep-csv` 导入 COMSOL 导出结果，那么：

- 谱线本身是真实 COMSOL 数据
- 摘要和筛选结果来自 Python 后处理
- 求解过程仍发生在 COMSOL 外部

## 下一步建议

当前最推荐的推进方式是：

1. 继续导出更多 COMSOL 光栅谱
2. 用联合扫描模式快速缩小周期范围
3. 锁定候选点后，再小范围细扫 `period / h_wg / fill_factor`
