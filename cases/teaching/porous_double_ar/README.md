# 多孔二氧化硅双层减反结构

## 1. 物理对象

低折射率多孔层与较高折射率匹配层组合，用于形成更平滑的空气到玻璃折射率过渡。

## 2. 推荐比较量

- `R(lambda)`
- 宽带平均反射率
- 厚度误差和折射率误差敏感性

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case porous_double_ar
```

## 5. 结果判断

重点比较双层多孔减反结构和普通单层减反结构的带宽差异。
