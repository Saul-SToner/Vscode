# 皱褶滤光片

## 1. 物理对象

折射率沿厚度方向连续或离散近似变化的 rugate 结构，用于展示非均匀膜层的光谱选择性。

## 2. 推荐比较量

- `R(lambda)`
- 阻带中心
- 阻带形状
- 与离散 QW 膜堆的差异

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case rugate_filter
```

## 5. 结果判断

重点说明 rugate 是渐变折射率思想，Python 中通常用多层离散近似实现。
