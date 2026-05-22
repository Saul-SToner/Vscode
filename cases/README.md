# cases 目录

`cases/` 按专题收纳具体运行脚本。仓库根目录只保留少量公开入口；高级专题统一通过 `run_case.py` 转发到 `cases/*/run_*.py`。

推荐理解方式：

```text
根目录公开 run_*.py  少量稳定入口
run_case.py          高级专题统一入口
cases/*/run_*.py    具体专题运行代码
cases/*/*/README.md 具体案例说明页
thinfilm/           薄膜教学、验证和研究分析库
guided_grating/     光栅波导支线库
```

每个具体脚本顶部都带有轻量路径引导，用于在直接运行 `cases/*/run_*.py` 时自动把仓库根目录加入 Python 导入路径。常用公开入口可以直接运行，高级专题推荐走 `run_case.py`：

```bash
python run_teaching_demo.py --list
python run_case.py --group pdrc --case cooling_bundle -- --comsol-csv "path/to/pdrc.csv"
python run_case.py --group tamm --case reflection_phase_screen -- --csv "path/to/tamm_scan.csv"
```

## 总索引

| 专题 | 定位 | 稳定入口 | 说明页 |
| --- | --- | --- | --- |
| `teaching/` | 教学主树、教学验证和性能总包 | `python run_teaching_demo.py --list` | `teaching/README.md` |
| `guided_grating/` | 光栅波导支线，读取 COMSOL 光谱并提取峰位/FWHM | `python run_guided_grating_demo.py` | `guided_grating/README.md` |
| `advanced_ar/` | 高级减反、多孔双层、蛾眼和 rugate 表格 | `python run_case.py --group advanced_ar --case bundle` | `advanced_ar/README.md` |
| `absorbing_surface/` | 粗糙/准随机吸收表面增强分析 | `python run_case.py --group absorbing_surface --case topic_bundle` | `absorbing_surface/README.md` |
| `tamm/` | Tamm 相位、1D 端结构筛选和界面态窗口分析 | `python run_case.py --group tamm --case reflection_phase_screen` | `tamm/README.md` |
| `pdrc/` | PDRC 被动日间辐射冷却光谱调控 | `python run_case.py --group pdrc --case cooling_bundle` | `pdrc/README.md` |
| `frontier/` | 前沿研究模型树 | `python run_frontier_model_tree.py --show` | `frontier/README.md` |
| `materials/` | 真实材料 n(lambda), k(lambda) 统一读取、插值与示例对比 | `python run_material_library_demo.py` | `materials/README.md` |

## 案例说明页约定

具体案例文件夹主要承担“展示说明”的职责，不一定每个文件夹都有独立 Python 脚本。许多平面膜案例由 `thinfilm/education.py` 统一定义，并通过 `run_teaching_demo.py --case <case_id>` 调用。

每个案例 README 优先按六段式组织：

1. 物理对象。
2. 结构参数。
3. 推荐比较量。
4. COMSOL 导出要求。
5. Python 运行方式。
6. 结果判断。
