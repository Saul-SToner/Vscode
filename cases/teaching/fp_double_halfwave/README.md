# 双半波型 F-P 滤光片

## 1. 物理对象

腔层光学厚度增加到两个半波量级的 F-P 滤光片，用于展示腔阶数变化。

## 2. 推荐比较量

- `T(lambda)`
- 共振峰数量或位置
- 与单半波腔的差异

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S21)^2`
- 可选：`abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case fp_double_halfwave
```

## 5. 结果判断

重点比较腔阶数增加后谱线位置和峰形的变化。
