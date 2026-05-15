# 四分之一波长 QW 膜堆

## 1. 物理对象

高低折射率四分之一波长层周期堆叠，是布拉格反射镜和高反膜的基础模型。

## 2. 推荐比较量

- `R(lambda)`
- 高反射带峰值
- 高反射带宽
- 周期数对反射率的影响

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case quarter_wave_stack
```

## 5. 结果判断

重点观察周期数增加后，高反射带是否变高并逐渐变陡。
