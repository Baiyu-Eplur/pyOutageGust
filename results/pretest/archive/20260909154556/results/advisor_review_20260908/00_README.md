# 工作命令 #56 — 导师模型探索材料：完整阅读与严格审查

审查对象：`pyOutageGust/Comments/Comments_for_Haoyan/STST2603_review/`（含 `Model_exploration_predicted_vs_observed.docx`、`Extended_paper_draft.docx`、`NatComms_extract_draft.docx`、`Paper_reorganisation_plan.docx` 四份 Word 文档 + `STST2603_review.zip` 解压出的完整代码/数据/结果包）。全程只读访问该包，未修改包内任何文件；所有独立验证脚本运行在本目录 `verification/` 下，未覆盖包内已有的 `results/`。

## 文件索引

| 文件 | 内容 |
|---|---|
| [`01_docx_reading_summary.md`](01_docx_reading_summary.md) | Step 1：三份 Word 文档（含 Paper_reorganisation_plan.docx）通读总结，与 MODEL_SELECTION_REPORT.md 的比较 |
| [`02_code_review.md`](02_code_review.md) | Step 2：12 个 `code/*.py`（+2 个 `.js`）逐行审查，含发现的所有代码级问题 |
| [`03a_placeholder_verification.md`](03a_placeholder_verification.md) | 3a 独立复现：占位符数据问题（最高优先级） |
| [`03b_knot_spline_verification.md`](03b_knot_spline_verification.md) | 3b 独立复现：结点/样条分歧（最高优先级，关键的更高自由度样条检验） |
| [`03c_lad_fe_verification.md`](03c_lad_fe_verification.md) | 3c 独立复现：LAD 固定效应"陷阱" |
| [`03d_district_day_panel_verification.md`](03d_district_day_panel_verification.md) | 3d：district-day 脆弱性面板构造有效性 |
| [`03e_fragility_methodology_verification.md`](03e_fragility_methodology_verification.md) | 3e 独立复现：脆弱性曲线方法论论证 |
| [`03f_remaining_scripts.md`](03f_remaining_scripts.md) | 3f：其余脚本通读汇总 |
| [`04_step3_claims_audit.md`](04_step3_claims_audit.md) | **Step 3：Claims audit 表格全部 11 条的三档分类结论（核心交付物）** |
| `verification/` | 全部独立验证脚本（3a/3b/3c 三个从零独立编写的 Python 脚本）+ 运行产出的 JSON 结果文件 |

## 一句话结论

导师材料的核心主张（二次型是错误函数形式、需要分段线性/结点估计；占位符数据问题真实存在且应剔除；LAD 固定效应是陷阱；district-day 面板方法论正确；weather-only 子样本揭示 composition 效应）**在最高优先级的两项独立复现（3a、3c）里得到精确数字级别的确认**；3b（结点/样条分歧，最挑剔的一项检验）**结论混杂**——高自由度样条确认了"二次型不是最优形式"这个方向，但没有支持"我们原来的样条被过度平滑"这一具体解释，建议论文调整这部分的论证方式；3d/3e 审查通过；3、9、11 三处受限于时间未完成从零独立复现，已在各自小节里明确标注卡在哪里、需要什么后续工作。**没有发现任何一条被彻底推翻的核心主张**。

## 验收标准对照

- [x] 3a、3b 两项最高优先级：均给出可追溯的独立复现数字（`verification/3a_results.json`、`verification/3b_results.json`），不是转述导师报告里的数字。
- [x] 3b 的"更高自由度样条"检验实际执行（df=4/6/8/10）并报告结果，含与导师报告不完全一致之处的如实说明。
- [x] Step 3 三档分类覆盖 Claims audit 表格全部 11 条，逐条给出依据。
