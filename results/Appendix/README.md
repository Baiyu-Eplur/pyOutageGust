# A–J 附录产物入口

本目录由main_appendix.py管理；只保留当前状态，历史研究输出仍留在原运行目录。

复现：`python main_appendix.py --all`；选择：`python main_appendix.py --appendices A J`；只读检查：`python main_appendix.py --all --check-only`。

正文权威来源：`results/new/20260909183317/results/paper/Extended_paper_draft.docx`。设计依据：`docs/new_analysis/instructions/论文整合计划_v9_附录成文与正文衔接.md`。段落P编号按DOCX直接body段落计数（包含空段）。

三层映射依次记录主张、需求、权威产物；单一可编辑登记源为analysis_new/appendix/catalog.py。图表显示编号仅在figure_table_register.csv维护。

当前表格70张（每表CSV+MD），图片9张。缺口见[result_gaps.md](result_gaps.md)。

|附录|本次选择|实际产物状态|范围|
|---|---|---|---|
|[A](A/README.md)|False|success_with_gaps|样本/变量、固定设计VIF和既有原因十分位表可整理；正文91%端点的分箱来源仍未定位。|
|[B](B/README.md)|False|success|构造证据与当前固定输入描述分开保存；历史清理范围不可替代当前样本。|
|[C](C/README.md)|False|success|最终四样本完整阶梯及同控制阵风函数；兼容组件复用、缺项补算，历史固定结点与D不同控制项另表。|
|[D](D/README.md)|False|success|只整理既有结点profile/bootstrap/nested结果；不新增稳定性结论。|
|[E](E/README.md)|False|success|Table 8是两个时期各自估计；不能称为冻结模型的后续预测。|
|[F](F/README.md)|False|success|四组最终系数与既有增量R²保留；F02仅补齐两个天气固定最终模型的LAD/date推断对照。|
|[G](G/README.md)|False|success|第三包结果缺口由负责人关闭；保存四组固定模型底层证据，GI-W图文待改保留。|
|[H](H/README.md)|True|success|第四包当前全体样本四项固定规格替代GLM及既有条件概率证据；有效性/例外逐项报告，待反馈。|
|[I](I/README.md)|False|success|第三包七风暴描述结果缺口由负责人关闭；GI-W图文待改保留。|
|[J](J/README.md)|False|success|ERA5聚合/持续性与正文proxy时间检验分开。八项时间BSS均为正，但校准和月度偏差保留；无新的通过阈值。|

运行只更新选定字母；暂存通过后事务替换，成功后移除仅此前清单管理的废弃文件。未知人工文件保留；若与新生成文件同名则报错而不覆盖。失败时保留上次完整产物并明确标注未更新。

科学范围：C/J03按已有授权，F02按第二包仅补天气固定模型聚类推断；其余仅整理。J03比较缺口由用户确认关闭；F02已由负责人关闭；G/I第三包结果缺口已关闭，图文待改保留；H03第四包仅既定四项GLM与条件概率整理，产物待反馈。
