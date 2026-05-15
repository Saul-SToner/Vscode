# 布拉格反射镜

## 1. 物理对象

由高低折射率周期膜层构成的高反射结构，用于形成中心波长附近的反射带隙。

## 2. 推荐比较量

- `R(lambda)`
- 中心反射率
- 反射带宽
- 带边位置

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_teaching_demo.py --case bragg_reflector
```

## 5. 结果判断

重点观察中心波长附近是否形成高反射平台，以及带边是否与理论趋势一致。
