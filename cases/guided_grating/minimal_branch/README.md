# 光栅波导最小支线

## 1. 物理对象

周期光栅与波导共振相关的研究支线，用于读取 COMSOL 光谱并进行峰位、FWHM 和参数筛选。

## 2. 推荐比较量

- `R(lambda)`
- `T(lambda)`
- 峰位
- FWHM
- 最接近目标波长的参数点

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- 参数列，如 `period` 或 `fill_factor`
- `R`
- `T`

## 4. Python 运行方式

```bash
python run_guided_grating_demo.py
python run_guided_grating_demo.py --sweep-csv "path/to/sweep.csv" --target-wavelength 1550
```

## 5. 结果判断

注意当前 Python 不是完整 RCWA/FEM 求解器；正式物理结果来自 COMSOL，Python 负责数据管线和指标提取。
