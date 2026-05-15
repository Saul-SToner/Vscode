# 教学主树案例

这里放教学平台主线的运行脚本。

常用根目录入口：

```bash
python run_teaching_demo.py --list
python run_teaching_demo.py --case single_ar
python run_teaching_demo.py --catalog
```

本目录内的具体脚本：

```text
run_teaching_demo.py
run_teaching_expansion_validation.py
run_teaching_metrics_bundle.py
```

## 具体案例说明

下面的子文件夹是案例说明页，不强制拆出独立 Python 代码。统一运行方式仍然是：

```bash
python run_teaching_demo.py --case <case_id>
```

例如：

```bash
python run_teaching_demo.py --case bragg_reflector
python run_teaching_demo.py --case fp_filter
python run_teaching_demo.py --case rugate_filter
```

案例说明页：

```text
single_ar/
double_ar/
triple_ar/
quarter_wave_single_layer/
half_wave_single_layer/
quarter_wave_double_layer/
high_reflector/
quarter_wave_stack/
bragg_reflector/
fp_filter/
fp_single_halfwave/
fp_double_halfwave/
narrowband_filter/
rugate_filter/
neutral_beamsplitter/
porous_sio2_layer/
porous_double_ar/
moth_eye_effective_gradient/
```
