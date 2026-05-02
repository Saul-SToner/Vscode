# data 目录说明

当前主目录 `data/` 不再存放反演样本。

原先用于厚度反演和偏振对照的样本，已经统一迁移到：

```text
archive/inversion_examples/
```

这样处理的目的有两个：

1. 让教学平台与 APP 主目录更干净
2. 保留研究样本，避免后续反演回归和支线验证断档

如果要继续使用反演主线，请优先从以下目录读取：

```text
archive/inversion_examples/deg.s
archive/inversion_examples/deg.p
archive/inversion_examples/deg.avg
```
