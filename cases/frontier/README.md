# 前沿研究模型树

这里放前沿研究模型树导出脚本，用于组织 Tamm、PDRC 等不直接放进教学主树首页的模块。

常用根目录入口：

```bash
python run_frontier_model_tree.py
python run_frontier_model_tree.py --bundle
```

当前导出包含：

```text
roadmap.json
roadmap.txt
roadmap.png
```

其中 `roadmap.png` 用于汇报展示，当前口径为：

```text
PDRC：正结果模块，已完成真实材料宽波段验证，A_solar_weighted(ASTM G173)=0.0435，epsilon_8_13_avg=0.8044，cooling_score_weighted=0.7609。
Tamm：前沿探索模块，已完成判据建立与候选排除，下一步转向 1D 反射相位端结构筛选。
```
