# 四分之一波长单层膜

## 1. 物理对象

一层光学厚度为 `lambda0/4` 的均匀薄膜，典型结构为 `Air / Layer / Glass`。

## 2. 推荐比较量

- `R(lambda)`
- 设计波长处反射谷
- 膜厚误差导致的谷位移动

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case quarter_wave_single_layer
```

## 5. 结果判断

重点说明厚度应为 `lambda0/(4*n_layer)`，不是几何厚度 `lambda0/4`。
