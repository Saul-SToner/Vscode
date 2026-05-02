# 光栅波导支线

本目录用于承接“异构薄膜 -> 光栅波导 -> 窄线宽反射镜设计”的支线。

当前状态：

1. 已搭好独立包结构
2. 已定义最小参数模型
3. 已接入谱线摘要与导出链路
4. 当前求解器仍是**明确标注的占位共振模型**

当前目标不是直接替代主树，而是先把支线工程骨架、输出格式和后续求解器接口稳定下来。

## 当前模块

```text
guided_grating/models.py
guided_grating/solver.py
guided_grating/spectra.py
guided_grating/export.py
guided_grating/examples.py
```

## 真实后续方向

后续可替换 `solver.py` 中的占位求解器，接入：

1. COMSOL 导出数据
2. RCWA
3. 其它更真实的周期结构求解器

## 重要说明

当前默认输出仅用于：

- 搭建分支结构
- 验证导出链路
- 给前端/平台预留统一接口

不应用于正式物理结论。
