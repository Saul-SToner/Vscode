# 中性分束膜

## 1. 物理对象

目标是在一定波段内获得近似固定分束比的薄膜结构。

## 2. 推荐比较量

- `R(lambda)`
- `T(lambda)`
- `R/T` 分束比例
- 吸收损耗 `A(lambda)`

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`
- `abs(ewfd.S21)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case neutral_beamsplitter
```

## 5. 结果判断

重点观察目标波段内分束比是否平坦，而不是只看单点结果。
