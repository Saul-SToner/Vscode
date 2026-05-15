# 80 层 Rugate 离散近似

## 1. 物理对象

用大量离散均匀薄层近似连续折射率调制的 rugate 滤光结构。

## 2. 推荐比较量

- `R(lambda)`
- 阻带中心
- 阻带宽度
- 离散层数带来的近似误差

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_rugate_80layer_table.py
```

## 5. 结果判断

重点说明 80 层结构用于近似连续渐变，展示价值高，但 COMSOL 建模和求解成本也更高。
