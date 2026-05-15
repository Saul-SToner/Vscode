# 三层减反射膜

## 1. 物理对象

三层介质薄膜构成的宽带减反结构，用于展示多层匹配带来的光谱调控能力。

## 2. 推荐比较量

- `R(lambda)`
- 宽带平均反射率
- 低反射区连续性

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case triple_ar
```

## 5. 结果判断

重点看三层膜是否比单层和双层结构形成更平滑的低反射窗口。
