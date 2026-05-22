# 二维周期准随机粗糙吸收表面

## 1. 物理对象

吸收材料表面的准随机粗糙结构，用于增强光程、散射和局域吸收。

## 2. 推荐比较量

- `A(lambda)`
- 增强因子
- 热点位置
- 粗糙度缩放比例

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`
- `1-abs(ewfd.S11)^2-abs(ewfd.S21)^2`
- 可选：粗糙度倍率

## 4. Python 运行方式

```bash
python run_case.py --group absorbing_surface --case topic_bundle
```

## 5. 结果判断

重点看粗糙结构相对平面吸收材料是否提高平均吸收，而不是只追求单点峰值。
