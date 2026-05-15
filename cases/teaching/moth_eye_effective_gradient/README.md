# 蛾眼结构等效渐变层

## 1. 物理对象

将亚波长蛾眼结构近似为多层有效折射率渐变膜，用于减小空气到基底的折射率突变。

## 2. 推荐比较量

- `R(lambda)`
- 宽带平均反射率
- 渐变层数对曲线平滑性的影响

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case moth_eye_effective_gradient
```

## 5. 结果判断

重点说明该案例是蛾眼结构的一维等效渐变版本，和显式二维梯形周期结构要分开讨论。
