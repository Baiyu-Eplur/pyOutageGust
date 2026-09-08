# 写入与保护范围

本轮唯一输出根：`D:\Pyprogramme\STST2603\claude_branch\paper_revision_work_v2`。code 为本轮核查代码及冻结快照，checks 为针对性数据核查，inventory/contracts/reports 为接收、规则和反馈。R00/R01不生成修正模型、派生正式样本或新天气请求。

受保护：父目录 data/、rebuild_v3_full_stage/（数据、脚本、日志）、旧天气 pkl/SQLite、分支既有 scripts/ 和 results/、docs/、所有论文 Word/Markdown、LOG.md、handoff 包。R02/R03 按后续授权将活动代码接入统一新入口；此前只保存快照。不得直接执行写死旧输出路径的历史生产者。

准备下一阶段入口：显式传入 raw/v3/cache、output_root、run_id、baseline_config；读取天气仅用 cache-only 适配器，禁止 CachedSession；统一 event table 作为所有消费者唯一样本入口；每次写入验证 resolve 后位于本轮根；保留输入 SHA/源行ID/排除理由。当前尚未实现这些修复接口。

保护证据：checks/protected_files_start.json；阶段结束增量重验相同549文件并验91源码来源/副本。原始大文件本轮已重算哈希，结束仅复核size/mtime，不重复1GB扫描；缓存针对本轮实际读取文件校验。
