# 二分之一波长单层膜

## 1. 物理对象

一层光学厚度为 `lambda0/2` 的均匀薄膜，用于和四分之一波长单层膜对比相位条件。

## 2. 推荐比较量

- `R(lambda)`
- 设计波长处反射行为
- 与 `quarter_wave_single_layer` 的差异

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case half_wave_single_layer
```

## 5. 结果判断

重点看半波厚度不会简单复现四分之一波长减反谷，而是体现不同相位叠加条件。
