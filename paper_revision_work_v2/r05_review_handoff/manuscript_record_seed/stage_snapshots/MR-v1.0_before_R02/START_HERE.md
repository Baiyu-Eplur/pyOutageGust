# 论文修订记录包

主入口：MANUSCRIPT_LEDGER.md。当前检查点为R00–R01已返回，R02尚未收到结果。

把本目录初始化到本地 `paper_revision_work_v2/manuscript_record/`。若已有更新台账，增量合并，不能覆盖。REVISION_ITEMS.json与主MD是同一批28项的结构化和可读形式，修改时保持一致。

evidence/保存输入快照，SOURCE_MANIFEST保存身份；D/A_word_index用于定位固定版本Word。段落索引只服务这两份归档Word，数学文本抽取不替代原公式或图片检查。

每个R/V/W阶段读取主台账，并按§7写稿件影响表、更新故事/逐章方案、追加CHANGELOG和阶段快照。代码报告不能替代写作记录；R/V更新计划不等于提前改Word。

新返回摘要/契约/证据请分配新来源ID，不覆盖SRC02或同名历史RETURN。所有候选句与结构建议都要按生效条件、作者决定和实际模型证据落实。
