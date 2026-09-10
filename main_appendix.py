"""附录产物生产入口；不启动 main_new.py 的研究步骤。"""
from analysis_new.appendix.runner import main

# 默认不写入；必须显式选择 --appendices A J 或 --all。
# --check-only 只检查来源和需求，不生成、清理产物或追加日志。
# --appendices C 接入APP-C-COMPLETE；--recompute-c 忽略C新计算缓存，重算缺失组件。
# --appendices J --j03-only 仅补齐/导出J03；--recompute-j03 明确重算本包96组件，其他J结果保留。
# --appendices F --f02-only 仅补齐天气固定final模型聚类协方差；--recompute-f02 重算协方差，优先复用兼容残差。
# --appendices G I --gi-only 补齐第三包预测/残差与七风暴；--recompute-gi仅重算本包，--render-only-gi仅用有效缓存重绘。
# --appendices H --h03-only 执行第四包固定规格替代分布与条件概率证据整理；--recompute-h03仅重算本包。
if __name__ == '__main__':
    raise SystemExit(main())
