# Tamm 界面拼接窗口

## 1. 物理对象

将两个 Tamm 候选参数区域在空间上拼接，用于观察边界附近的场增强和热点定位。

## 2. 推荐比较量

- `normE`
- `normE^2`
- 局域热点中心
- 局域宽度
- 增强因子

## 3. COMSOL 导出要求

推荐使用二维 Grid 或 Cut Line 数据集导出：

- `x`
- `y`
- `lambda`
- `ewfd.normE`
- 可选：`ewfd.Qh`

## 4. Python 运行方式

```bash
python run_tamm_interface_window_bundle.py
python run_tamm_interface_window_scan.py
```

## 5. 结果判断

重点量化热点是否聚集在拼接界面附近，而不是只依赖场图的主观观感。
