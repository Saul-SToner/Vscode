# F-P 滤光片

## 1. 物理对象

Fabry-Perot 腔型滤光片，由两个反射镜和中间腔层构成，用于形成窄透射峰或反射谷。

## 2. 推荐比较量

- `T(lambda)`
- `R(lambda)`
- 共振峰位置
- 峰宽或 FWHM

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case fp_filter
```

## 5. 结果判断

重点观察腔长与透射峰位置的对应关系，以及反射镜强度对峰宽的影响。
