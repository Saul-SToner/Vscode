# Tamm 反射相位扫描

## 1. 物理对象

金属/介质多层膜组合中的 Tamm 态候选结构，用反射相位和吸收谱寻找边界态条件。

## 2. 推荐比较量

- `R(lambda)`
- `A(lambda)`
- `arg(S11)`
- 相位跳变
- 候选厚度参数

## 3. COMSOL 导出要求

推荐导出：

- `lambda`
- 扫描参数，如 `d_W`
- `real(ewfd.S11)`
- `imag(ewfd.S11)`
- `abs(ewfd.S11)^2`

## 4. Python 运行方式

```bash
python run_case.py --group tamm --case phase_bundle
python run_case.py --group tamm --case phase_candidates
```

## 5. 结果判断

重点看相位是否出现可解释的跳变，并结合吸收峰判断是否为稳定候选态。
