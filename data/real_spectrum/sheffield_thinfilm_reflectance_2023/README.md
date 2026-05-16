# Sheffield 薄膜反射测厚数据集

该目录为后续接入 Sheffield ORDA / figshare 公开数据集预留。

## 数据定位

用途：

- 真实反射谱拟合
- 薄膜厚度反演
- RMSE/MSE 指标验证

不建议第一阶段用于所有教学案例。教学案例优先使用 TMM 理论谱线和 COMSOL 对照，真实测量谱线作为独立验证模块更稳。

## 目录约定

```text
raw/        原始下载文件，不改列名
processed/ 统一格式后的 CSV
```

统一格式建议：

```csv
lambda_nm,R_exp,sample_id,source
400,0.123,sample_01,Sheffield_ORDA_2023
```

## 来源

- 论文：https://doi.org/10.3390/s23115326
- 数据 DOI：https://doi.org/10.15131/shef.data.23285603
