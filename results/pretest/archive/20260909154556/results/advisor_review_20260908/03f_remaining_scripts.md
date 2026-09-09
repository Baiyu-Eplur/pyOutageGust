# 3f — 其余脚本通读确认

`plateau_model.py`、`paper_extras.py`、`plot_model_selection.py`、`weather_only_regression.py`、`build_doc.js`、`build_papers.js` 六个脚本已在 Step 2（[`02_code_review.md`](02_code_review.md)）里逐行读过，此处不重复，只汇总要点：

- **`plateau_model.py`**：逻辑无误，发现一处 print 语句 BIC 参数计数笔误（不影响保存结果）和一处更重要的"`knots.json` 的 `selected`/`form` 字段无法被当前打包的 `code/` 完整复现"的 provenance 缺口——详见 02 review。
- **`paper_extras.py`**：development/confirmation 切分与变量组 R² 分解逻辑清楚，没有发现问题。
- **`plot_model_selection.py`**：出图脚本，读取的是已经正确更新过的 `knots.json`（[14,25]），图表数字与正文一致，没有问题。
- **`weather_only_regression.py`**：复用 `knot_estimation.py` 的 `KnotSolver`/`hinge_cols`（没有重复实现一遍数学逻辑，好的工程实践），依赖 `plateau_model.py` 产出的 `ramp_model.json`，执行顺序隐式（通过磁盘文件而非显式参数传递），风格上可以更清楚但不算错误。
- **`build_doc.js`/`build_papers.js`**：纯文档组装，图表数据从 JSON 动态读取，正文段落是硬编码字符串——不会随数据重跑自动更新，是长期维护风险，不是当前的错误。

**未发现推翻任何核心结论的问题**。唯一值得导师团队关注的是 `plateau_model.py` 的可复现性缺口（见 02 review 详细说明），建议打包前确认 `code/` 目录里的脚本版本与 `results/` 目录的产出严格对应。
