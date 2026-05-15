# 高反射膜

## 1. 物理对象

由高低折射率多层膜构成的高反结构，用于在目标波段获得较高反射率。

## 2. 推荐比较量

- `R(lambda)`
- 峰值反射率
- 高反带宽
- 周期数或层数影响

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case high_reflector
```

## 5. 结果判断

重点观察目标波段是否形成稳定高反射平台，并和布拉格反射镜、四分之一波长膜堆进行对照。
