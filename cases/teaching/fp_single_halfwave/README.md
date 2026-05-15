# 单半波型 F-P 滤光片

## 1. 物理对象

中间腔层为单个半波光学厚度的 F-P 滤光片，是最基础的腔模案例。

## 2. 推荐比较量

- `T(lambda)`
- 共振透射峰位置
- FWHM

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S21)^2`
- 可选：`abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case fp_single_halfwave
```

## 5. 结果判断

重点看半波腔是否在设计波长附近给出透射共振。
