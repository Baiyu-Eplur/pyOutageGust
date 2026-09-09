"""导师分析独立复现入口：修改本文件顶部参数后运行 python main_new.py。"""

# 每次运行必须说明目的；0 关闭，1 开启。依赖缺失时明确报错，不偷偷补跑。
RUN_PURPOSE = '完整复现导师分析：自己的相同样本、500 次结点与 300 次平台 bootstrap'
DRY_RUN = 0
REUSE_RUN = ''  # 可填写 results/new 下已完成运行的时间戳；校验后复用其产物。
KNOT_BOOTSTRAPS = 500
PLATEAU_BOOTSTRAPS = 300
BLAS_THREADS = 1
STEPS = {
    'baseline': 1,
    'model_selection': 1,
    'hinge_search': 1,
    'knot_estimation': 1,
    'plateau_E0': 1,
    'plateau_R0c': 1,
    'select_final_knots': 1,
    'plot_model_selection': 1,
    'fragility_demo': 1,
    'fragility_surfaces': 1,
    'final_models': 1,
    'district_day_fragility': 1,
    'weather_only_regression': 1,
    'paper_extras': 1,
    'report_tables': 1,
    'documents': 1,
}


def main():
    from analysis_new.runner import run
    return run(STEPS, RUN_PURPOSE, dry_run=DRY_RUN, reuse_run=REUSE_RUN,
               knot_bootstraps=KNOT_BOOTSTRAPS, plateau_bootstraps=PLATEAU_BOOTSTRAPS,
               blas_threads=BLAS_THREADS)


if __name__ == '__main__':
    raise SystemExit(main())
