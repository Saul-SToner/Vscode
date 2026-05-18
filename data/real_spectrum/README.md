# 真实反射谱数据

本目录用于后续接入公开实测薄膜反射谱。第一批建议只接入厚度反演或真实反射谱拟合模块，不强行塞进每个教学案例。

推荐统一格式：

```csv
lambda_nm,R_exp,sample_id,source
400,0.123,sample_01,Sheffield_ORDA_2023
```

## 候选数据集

Sheffield ORDA / figshare 数据集，对应论文：

- N. E. Sánchez-Arriaga et al., A Spectroscopic Reflectance-Based Low-Cost Thickness Measurement System for Thin Films: Development and Testing, Sensors 23(11), 5326 (2023). https://doi.org/10.3390/s23115326
- 论文 Data Availability Statement 给出的数据 DOI: https://doi.org/10.15131/shef.data.23285603

该数据集更适合验证真实测量反射谱处理、厚度拟合、RMSE/MSE 指标，而不是替代每个教学案例的理论曲线。

## 太阳光谱权重

PDRC 模块当前支持两种太阳波段平均方式：

- 普通算术平均：`A_solar_avg`
- 太阳光谱加权平均：`A_solar_weighted`

默认加权模式为 `blackbody_5778K`，用于第一版快速判断短波紫外吸收峰是否显著影响太阳平均吸收。当前 PDRC 正式结果已接入 ASTM G173-03 AM1.5 global tilt 标准太阳光谱，文件位于：

```text
data/real_spectrum/astm_g173_am15/astm_g173_am15_global_tilt.csv
```

外部光谱 CSV 推荐整理为：

```csv
lambda_um,irradiance
0.300,0.0
0.305,0.0
```

然后在命令行中使用：

```bash
python run_pdrc_cooling_bundle.py --analyze-comsol-candidates --solar-weight-csv "path/to/solar_spectrum.csv"
```
