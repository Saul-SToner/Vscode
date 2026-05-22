# 普通 Tamm 吸收器基线

## 1. 物理对象

金属层与一维介质光子晶体或多层膜组合形成的 Tamm 吸收结构。该基线用于先确认单侧周期结构可以在目标红外波段形成吸收特征。

## 2. 结构参数

推荐先固定一组候选参数：

```text
d_W = 110-120 nm  # 示例候选范围
lambda = 4.2-5.0 um
```

其他层厚和材料保持与当前 Tamm 模型一致。

## 3. 推荐比较量

- `R(lambda)`
- `A(lambda) = 1 - R(lambda) - T(lambda)`
- 吸收峰位置
- 吸收峰宽度

## 4. COMSOL 导出要求

推荐导出：

- `lambda`
- `d_W`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`
- `1-abs(ewfd.S11)^2-abs(ewfd.S21)^2`

## 5. Python 运行方式

```bash
python run_case.py --group tamm --case phase_bundle -- --csv "path/to/tamm_scan.csv"
```

## 6. 结果判断

第一版目标是找到稳定吸收峰，并确认峰位不会因为过粗的参数步长而被误判。
