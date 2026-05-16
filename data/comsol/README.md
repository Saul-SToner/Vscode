# COMSOL 数据目录

本目录用于说明 COMSOL 导出数据的组织方式。大型参数扫描结果建议留在本机实验目录或 `~/thinfilm_outputs`，仓库中只放小型示例或说明。

推荐专题结构：

```text
quarter_wave_single_layer/
bragg_reflector/
fp_filter/
narrowband_filter/
pdrc/
tamm/
```

推荐导出列：

- `lambda`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`
- `1-abs(ewfd.S11)^2-abs(ewfd.S21)^2`
- 参数扫描列，如 `d_layer`、`d_W`、`theta`
