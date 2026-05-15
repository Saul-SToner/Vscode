# 双层减反射膜

## 1. 物理对象

两层介质薄膜构成的减反射结构，用于比单层膜获得更宽或更深的低反射区。

## 2. 推荐比较量

- `R(lambda)`
- 低反射带宽
- 设计波长附近平均反射率

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case double_ar
```

## 5. 结果判断

重点观察双层结构是否相对单层减反膜拓宽低反射区。
