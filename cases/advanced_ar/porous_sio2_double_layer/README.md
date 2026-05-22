# 多孔 SiO2 双层减反专题

## 1. 物理对象

多孔 SiO2 低折射率层与致密 SiO2 或匹配层组合，用于构建空气到玻璃之间的双层折射率过渡。

## 2. 推荐比较量

- `R(lambda)`
- 宽带平均反射率
- `n_porous` 和 `d_porous` 敏感性
- 入射角扫描结果

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`
- 可选：参数列，如 `n_porous`、`d_porous`、`theta`

## 4. Python 运行方式

```bash
python run_case.py --group advanced_ar --case porous_double_ar
```

## 5. 结果判断

重点看低折射率层是否显著压低反射率，以及误差扫描是否说明结构具有一定容差。
