"""导师分析独立复现入口：修改本文件顶部参数后运行 python main_new.py。"""

# 每次运行必须说明目的；0 关闭，1 开启。依赖缺失时明确报错，不偷偷补跑。
RUN_PURPOSE = 'DD-AGG01：固定 ERA5 网格、标签、模型与 LAD 折号，比较五种日度阵风聚合'  # 记录本次运行目的。
DRY_RUN = 0  # 1 仅打印将执行的步骤；0 按下面的开关执行。
REUSE_RUN = ''  # 可填写 results/new 下已完成运行的时间戳；校验后复用其产物。
KNOT_BOOTSTRAPS = 500  # 原结点估计的 LAD bootstrap 次数。
PLATEAU_BOOTSTRAPS = 300  # 原平台估计的 LAD bootstrap 次数。
BLAS_THREADS = 1  # 每个分析子进程的数值计算线程数。

# P03/P04 独立实验参数；不需要开启旧步骤或设置 REUSE_RUN。
P03_BASE_RUN = '20260909183317'  # 已完成的旧面板所在运行，按清单校验后只读使用。
P03_WEATHER_CACHE_RUN = ''  # 可填上次 P03 运行编号，复用校验通过的 API 原始响应（支持失败运行）。
P03_REQUEST_INTERVAL_SECONDS = 10  # 相邻 LAD 请求间隔；每个 LAD 一次完整日期范围请求。
P03_BOOTSTRAPS = 1000  # 对已生成的折外误差做 LAD 配对 bootstrap，不反复拟合模型。
P03_MIN_REL_BRIER_GAIN = 0.05  # 候选有意义改善门槛：8 个任务平均相对 Brier 改善至少 5%。
DD_AGG01_SOURCE_RUN = '20260909205214'  # 只读复用本轮 P03 已下载小时天气、面板和固定 LAD 折号。
DD_DUR01_BASE_RUN = '20260909231634'  # 持续性实验复用的已修复 A01 参数、折外预测及协议。
DD_DUR01_WEATHER_RUN = '20260909205214'  # 持续性实验只读复用的小时 ERA5、原标签和 LAD 折号。
DD_DUR01_PURPOSE = 'DD-DUR01：日最大阵风与超阈小时比例/平方累计指标的增量测试'  # 单独开启持续性实验时记录的目的。
DD_TIME01_SOURCE_RUN = '20260909183317'  # 正文生产运行；读取其原事件锚点插值proxy面板，不读取ERA5替换面板。
DD_TIME01_PURPOSE = 'DD-TIME01：正文proxy固定规格回顾性时间留出，仅开发期拟合并冻结预测'  # 单独开启时间检验时记录的目的。
STEPS = {
    'baseline': 0,  # 复用旧主回归，生成 E0/R0c 基准系数及稳健标准误。
    'model_selection': 0,  # 比较 12 种模型形式及随机、LAD、年份交叉验证。
    'hinge_search': 0,  # 比较固定单/双/三铰链候选模型。
    'knot_estimation': 0,  # 正式估计自由铰链结点、bootstrap 区间与嵌套验证。
    'plateau_E0': 0,  # E0 全体/天气子样本平台结点估计及 bootstrap。
    'plateau_R0c': 0,  # R0c 正客户数全体/天气子样本平台模型探索。
    'select_final_knots': 0,  # 区分探索结点与最终平台结点，写回选择记录。
    'plot_model_selection': 0,  # 绘制模型比较、预测与观测、校准及残差图。
    'fragility_demo': 0,  # 事件条件下有序 logit、阈值 logit 和负二项演示。
    'fragility_surfaces': 0,  # 事件条件下对数正态脆弱性曲线和 probit 曲面。
    'final_models': 0,  # 最终 E0 平台/R0c 二次回归；仅 R0c 排除零客户事件。
    'district_day_fragility': 0,  # 原区域日面板：事件天气插值代理、脆弱性与曲面。
    'weather_only_regression': 0,  # 天气归因事件子样本的模型、结点与预测验证。
    'paper_extras': 0,  # 时间分样、交叉验证 R² 分解与响应分布。
    'report_tables': 0,  # 从当轮结果生成表格 JSON 和 Markdown 计算摘要。
    'documents': 0,  # 使用自有原稿素材生成四份 Word 文档。
    'p03_p04_grid_weather': 0,  # 独立实验：ERA5 日最大阵风替换代理，8 阈值拟合、LAD-CV 与判定。
    'dd_agg01': 0,  # 独立实验：先统一修复优化，再比较五种日度聚合的 240 个拟合及折外验证；不联网。
    'dd_dur01': 0,  # 独立实验：训练折天气90%阈值，M0/M1/M2拟合、折外评价和技术核验；不作模型采用裁决。
    'dd_time01': 0,  # 独立实验：2023-09-30前开发拟合、之后冻结预测，8任务评分/校准/月度摘要及技术核验。
}


def main():
    from analysis_new.runner import run
    purpose = DD_DUR01_PURPOSE if STEPS['dd_dur01'] and sum(STEPS.values()) == 1 else RUN_PURPOSE
    if STEPS['dd_time01'] and sum(STEPS.values()) == 1:
        purpose = DD_TIME01_PURPOSE
    return run(STEPS, purpose, dry_run=DRY_RUN, reuse_run=REUSE_RUN,
               knot_bootstraps=KNOT_BOOTSTRAPS, plateau_bootstraps=PLATEAU_BOOTSTRAPS,
               blas_threads=BLAS_THREADS,
               p03_settings=dict(base_run=P03_BASE_RUN, weather_cache_run=P03_WEATHER_CACHE_RUN,
                                 request_interval=P03_REQUEST_INTERVAL_SECONDS,
                                 bootstraps=P03_BOOTSTRAPS, min_relative_gain=P03_MIN_REL_BRIER_GAIN),
               dd_agg01_settings=dict(source_run=DD_AGG01_SOURCE_RUN),
               dd_dur01_settings=dict(base_run=DD_DUR01_BASE_RUN, weather_run=DD_DUR01_WEATHER_RUN),
               dd_time01_settings=dict(source_run=DD_TIME01_SOURCE_RUN))


if __name__ == '__main__':
    raise SystemExit(main())
