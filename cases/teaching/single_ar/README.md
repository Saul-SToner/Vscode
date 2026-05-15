# 单层减反射膜

## 1. 物理对象

单层均匀介质膜夹在空气与玻璃基底之间，用于展示最基本的相消干涉减反射。

## 2. 推荐比较量

- `R(lambda)`
- 最小反射率
- 设计波长附近的反射谷位置

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`
- 可选：`abs(ewfd.S21)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case single_ar
```

## 5. 结果判断

重点看反射谷是否出现在设计波长附近，以及理论曲线与 COMSOL 曲线的峰谷位置是否一致。
