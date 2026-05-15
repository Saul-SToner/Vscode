# 窄带滤光片

## 1. 物理对象

高反射膜与谐振腔组合形成的窄带滤光结构，用于在宽阻带中打开窄透射窗口。

## 2. 推荐比较量

- `T(lambda)`
- 峰值透射率
- FWHM
- 峰位偏移

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S21)^2`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case narrowband_filter
```

## 5. 结果判断

重点观察透射窗口是否足够窄，以及峰位是否稳定落在目标波长附近。
