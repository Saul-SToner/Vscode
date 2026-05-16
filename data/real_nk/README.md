# 真实材料光学常数库

本目录第一批接入 RefractiveIndex.INFO 的公开材料光学常数，并统一成平台可读 CSV：

```csv
lambda_um,n,k,material,source
0.400,1.470,0.000,SiO2,Malitson
```

## 数据来源

来源数据库：

- RefractiveIndex.INFO database: https://github.com/polyanskiy/refractiveindex.info-database
- 数据库论文：Polyanskiy, M. N. Refractiveindex.info database of optical constants, Scientific Data 11, 94 (2024). https://doi.org/10.1038/s41597-023-02898-2

RefractiveIndex.INFO 数据库文件声明为 public domain / CC0，可用于复制、修改和分发。这里保留原始来源名称，便于追溯。

## 当前文件

| 文件 | 材料 | 来源 | 波长范围 |
| --- | --- | --- | --- |
| `SiO2_Malitson.csv` | SiO2 | Malitson 1965; Tan 1998 | 0.21-6.70 um |
| `TiO2_Devore_o.csv` | TiO2 | Devore 1951, ordinary ray | 0.43-1.53 um |
| `MgF2_Dodge_o.csv` | MgF2 | Dodge 1984, ordinary ray | 0.20-7.00 um |
| `Al2O3_Malitson_o.csv` | Al2O3 | Malitson 1962, ordinary ray | 0.20-5.00 um |
| `Au_Johnson_Christy.csv` | Au | Johnson and Christy 1972 | 0.1879-1.937 um |
| `Ag_Johnson_Christy.csv` | Ag | Johnson and Christy 1972 | 0.1879-1.937 um |
| `Si_Aspnes.csv` | Si | Aspnes and Studna 1983 | 0.2066-0.8266 um |

## 使用边界

这些文件优先用于教学主树、高反膜、F-P、Tamm 可见/近红外版本和材料色散演示。若用于中红外 PDRC 或 4-5 um Tamm，需要确认材料数据覆盖对应波段；例如 Johnson-Christy Au/Ag 不覆盖中红外长波段。

## 生成方式

公式型 YAML 数据按有效波段采样为 CSV，表格型 `nk` 数据保留原始采样点。`manifest.json` 记录每个文件的来源 URL、行数和波长范围。
