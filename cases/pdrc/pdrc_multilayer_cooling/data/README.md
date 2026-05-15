# PDRC data 目录

这里用于说明 PDRC 模块需要的数据类型。大型 COMSOL 扫描 CSV 不建议长期提交到仓库。

推荐数据类型：

- `comsol_solar.csv`：太阳波段 `0.3-2.5 um` 的 `R/T/A`。
- `comsol_ir.csv`：红外窗口 `8-13 um` 的 `R/T/A`。
- `solar_spectrum_reference.csv`：太阳光谱权重，可选。
- `atmosphere_window_reference.csv`：大气窗口权重，可选。

当前本机分析输出建议继续写入 `~/thinfilm_outputs`。
