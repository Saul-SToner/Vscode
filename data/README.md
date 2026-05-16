# 数据目录

本目录用于说明平台接入的外部数据和本地生成数据。当前数据分为三层：

```text
第一层：理论数据
由 TMM/特征矩阵法生成，用于验证公式、案例和导出链路。

第二层：COMSOL 数值仿真数据
由 Wave Optics 模块导出 R(lambda)、T(lambda)、A(lambda)，用于验证复杂结构和二维周期结构。

第三层：公开真实数据
包括真实材料光学常数 n(lambda), k(lambda)，以及后续接入的公开实测反射谱。
```

## 子目录

```text
real_nk/        公开材料光学常数，统一为 lambda_um,n,k,material,source
real_spectrum/ 公开实测反射谱数据说明和后续处理入口
comsol/         COMSOL 导出数据的专题占位目录
theory/         Python TMM 生成的理论谱线说明
```

大型 COMSOL 扫描 CSV 和批量图片不建议长期提交到仓库，默认输出仍放在 `~/thinfilm_outputs`。
