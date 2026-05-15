# 四分之一波长双层膜系

## 1. 物理对象

两层均为四分之一波长光学厚度的介质膜，典型结构为 `Air / L / H / Glass`。

## 2. 推荐比较量

- `R(lambda)`
- 中心波长反射率
- 双层与单层减反差异

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case quarter_wave_double_layer
```

## 5. 结果判断

重点检查两层厚度是否分别按 `lambda0/(4*n_low)` 和 `lambda0/(4*n_high)` 设置。
