# Step 1 — 三份 Word 文档通读总结

来源：`pyOutageGust/Comments/Comments_for_Haoyan/{Model_exploration_predicted_vs_observed,Extended_paper_draft,NatComms_extract_draft}.docx`，另外为了完成 Step 3 需要的 "Claims audit" 表，也一并提取了 `STST2603_review/STST2603_review/paper/Paper_reorganisation_plan.docx`。全部用 python-docx 按文档原始顺序逐 block（段落+表格）提取，图片位置用 `[IMAGE #n]` 占位标出，未跳过任何表格。提取文件：`Comments/Comments_for_Haoyan/extracted_*.md`（未写入 STST2603_review 包内，符合只读约束）。

## 1. Model_exploration_predicted_vs_observed.docx（14 页，14 张图/12 章）

核心论点：
- E0（暴露）响应是分段线性（flat→ramp→plateau），不是二次型；两个结点在 14 和 26 m/s（第 12 节的"plateau约束"版本把第二个结点重新profile到 25 m/s，见下）。ΔBIC = −129 vs 二次型，nested LAD-grouped CV 也改善。
- R0c（恢复）响应二次型/单结点(17 m/s)等价，没有第二个可识别的结点。
- LAD 固定效应模型样本内指标全面最优，但 LAD-grouped CV 是所有模型里最差的（calibration slope 只有 0.25/0.33）。
- Weather-only 子样本上 E0 是 V 形（不是二次型能拟合的），最低点在 11 m/s，上升斜率与全样本相近。
- 恢复样本里 8,661 个 zero-customer 事件，66.5% duration 恰好 1.000h，判定为占位符，建议从 R0c 样本剔除；剔除后 customers 系数符号翻转。
- 第 7b 节的核心方法论论证：事件条件下的超越概率不是真正的脆弱性曲线，因为 weather_natural 占比随阵风变化（7% at 0-4 m/s → 91% at 30+ m/s），这是一个 composition 而非 vulnerability 的证据；需要 district-day panel 才能定义真正的 fragility。
- 第 10 节：district-day panel（121,656 个 district-day），用高斯核 IDW（40km）从当天事件位置插值出 district gust，leave-district-out RMSE 2.2 m/s，r=0.85；拟合 background-rate lognormal fragility，θ 集中在 23-25 m/s（按 size threshold）、30+ m/s（>1000 customers）。
- **第 12 节（重要，且在 MODEL_SELECTION_REPORT.md 里完全没有 —— 属于文档间新增/不一致信息，见下）**：给暴露响应施加"plateau 约束"（第二个结点之外斜率强制为零），LR 检验不拒绝该约束（p=0.22），BIC 再改善 10；结点重新 profile 到 **14 和 25 m/s**（不再是 14/26）。**明确撤回第 11 节"weather-only 斜率与 pooled 斜率基本相同"的说法**：施加正确的 plateau 形式后，weather-only ramp 斜率（0.079）只有 pooled 斜率（0.121）的三分之二，即 pooled 上升里约 1/3 是 composition 效应、2/3 才是真正的 vulnerability——这和第 11 节原文"two-thirds... same as the full-sample hinge slope"的表述是**自相矛盾并被文档自己修正**的。R0c 侧的 plateau 检验被拒绝（p=0.003），说明恢复时长确实不封顶。

## 2. 与 MODEL_SELECTION_REPORT.md 的比较

`MODEL_SELECTION_REPORT.md` 只对应 docx 的第 1–11 节，**完全没有第 12 节的 plateau 约束修正**——即 .md 版本仍然停留在"E0 结点 14/26 m/s，weather-only 斜率与 pooled 基本相同"这个后来被 docx 自己撤回的结论上。.md 文件里有一张 docx 正文没有逐一复现的精确 BIC 数值表（第 4 节，`knot_estimation.py` 输出）：

| | E0 | R0c |
|---|---|---|
| 二次型 BIC（论文原版） | 83117.6 | 28474.1 |
| 单结点 BIC | 83021.7（ΔBIC −96，k=13） | 28462.8（ΔBIC −11，k=17） |
| 双结点 BIC | 82988.3（ΔBIC −129，k=14/26） | 28456.5（ΔBIC −18，k=14/20） |

这张表是我在 3b 独立复现时用作比对基准的关键数字来源之一。

**需要向导师/网页端 Claude 指出的一点**：docx 第 12 节自己说"final_models.py、weather_only_regression.py、plot_model_selection.py 和 paper_extras.py 现在都用三段式 plateau 形式"，但 Section 9/11 的旧 hinge 系数"保留作为无约束对比"——这意味着 `results/` 目录下不同文件之间可能混有 plateau 版（knots.json 更新后）和旧 unconstrained 版（ramp_model.json 分开存放）的结点数字，读表格时要认清楚具体是哪一版，Step 2 代码审查时会逐一核实。

## 3. Extended_paper_draft.docx / NatComms_extract_draft.docx

这两份是论文格式的重写稿，内容与 Model_exploration 文档、Paper_reorganisation_plan.docx 描述的结果**一致**（数字上使用的都是 plateau 约束后的最终版本：14/25 m/s，非 14/26），没有发现与 Model_exploration 文档矛盾之处。相比 Model_exploration 文档新增的内容：
- **Table 3（Extended paper）**：完整的 12 项 specification ladder ΔBIC + CV RMSE 对比表（比 Model_exploration 文档的叙述更完整，包含 gust step dummies 等未在正文详述的形式）。
- **Table 6（Extended paper）/ R² decomposition**：district-grouped CV 下按变量组（regional+calendar / non-gust weather / gust / customers）拆解的边际 R² 贡献，精确到 pp——这是 `paper_extras.py` 的产出，Model_exploration 文档里没有给出这张分解表的具体数字。
- **Table 8（development/confirmation split）**：ramp slope 在 dev（0.100±0.014）和 confirmation（0.149±0.020）两个子样本上的具体系数——Model_exploration 文档第 12 节只给了这两个数字的文字提及，Extended paper 给出了标准误。
- NatComms 版本的摘要明确写了"25 m/s (24–28)"而不是文档正文一处仍写"26 m/s"的地方——这印证了 plateau 版本（25 m/s）是导师团队最终认定的数字，Model_exploration 文档里散落的"26 m/s"字样（第 3、9、11 节，均在第 12 节的修正之前）应视为已被取代的旧版本表述，不是矛盾，而是文档内部的版本演进。

## 4. Paper_reorganisation_plan.docx

提取了完整的 "Claims audit"（Table 4，11 行）——Step 3 的三档分类将逐行覆盖这张表。此外这份文档还包含"Production plan"（第 5 节），列出了导师团队自己认为**尚未做完**的工作：development/confirmation split 的最终版重新拟合、变量组方差分解、危险度卷积（需要包外数据）、Fig 1-2 用剔除占位符后的数据重画、"重新检查 Appendix H 的样条对比"。这些"未完成项"里，"重新检查 Appendix H 样条对比"正是本审查 3b 的核心任务——说明导师团队自己也认为这一点需要进一步核实，不是一个已经盖棺定论的结论。
