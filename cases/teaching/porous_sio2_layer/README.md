# 多孔二氧化硅膜层

## 1. 物理对象

用有效折射率表示多孔 SiO2 膜层，作为低折射率减反材料。

## 2. 推荐比较量

- `R(lambda)`
- 最小反射率
- 有效折射率变化对反射谷的影响

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case porous_sio2_layer
```

## 5. 结果判断

重点说明该案例是等效介质模型，不是显式孔洞几何模型。
