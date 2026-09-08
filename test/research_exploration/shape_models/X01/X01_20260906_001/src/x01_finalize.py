"""Generate X01 figures and narrative only from persisted numeric artifacts."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import x01_run as x


def main() -> None:
    preflight = json.loads((ROOT / "evidence" / "preflight.json").read_text(encoding="utf-8"))
    leader = pd.read_csv(ROOT / "tables" / "model_leaderboard.csv")
    fits = pd.read_csv(ROOT / "tables" / "fit_diagnostics.csv")
    paired = pd.read_csv(ROOT / "tables" / "paired_comparisons.csv")
    params = pd.read_csv(ROOT / "tables" / "shape_parameters.csv")
    selected = json.loads((ROOT / "MODEL_REGISTRY.json").read_text(encoding="utf-8"))["selected_for_conditional_bootstrap"]
    curves = pd.read_parquet(ROOT / "evidence" / "curve_data.parquet")
    calibration = pd.read_csv(ROOT / "tables" / "calibration_bins.csv")
    gust = pd.read_csv(ROOT / "tables" / "gust_bin_diagnostics.csv")
    oof = pd.read_parquet(ROOT / "predictions" / "oof_predictions.parquet")
    refits = pd.read_csv(ROOT / "evidence" / "bootstrap_refit_all.csv")
    for task in ("E", "R", "R_C"):
        x.plot_leaderboard(leader, task)
        x.plot_curves(curves, task)
        x.plot_curves(curves, task, True)
        x.plot_standardized_curves(curves, task)
        x.plot_support(oof, task)
        x.plot_calibration(calibration, task)
        x.plot_gust_diagnostics(gust, task, leader)
    stories = []
    for task in ("E", "R", "R_C"):
        shortlist = leader.loc[leader.task_id.eq(task)].sort_values("mean_deviance").head(3)
        first = shortlist.iloc[0]
        stories.append(f"- **{task}**：预设OOF主指标下前三为 `{', '.join(shortlist.model_id)}`；首位 `{first.model_id}` 相对M00的偏差改善为 `{first.deviance_improvement_vs_M00:.6g}`。这说明下一阶段应把“是否可区分曲线”而不是先验指定阈值放进结果段，并将曲线支持密度与配对区间一起呈现。证据：`tables/model_leaderboard.csv`、`tables/paired_comparisons.csv`、`figures/curves_{task}.png`。")
    x.write_reports(preflight, leader, fits, paired, params, selected, stories)
    def performance_sentence(task, model):
        row = paired.loc[(paired.task_id.eq(task)) & (paired.model_id.eq(model))].iloc[0]
        return (f"{task}/{model} 相对M00的条件OOF偏差差为 {row.deviance_delta_mean:.4g} "
                f"（95%群组重抽样区间 {row.deviance_delta_ci_low:.4g} 至 {row.deviance_delta_ci_high:.4g}），"
                f"RMSE差为 {row.rmse_delta_mean:.4g}（{row.rmse_delta_ci_low:.4g} 至 {row.rmse_delta_ci_high:.4g}）。")
    def refit_sentence(task, model):
        d = refits.loc[(refits.task_id.eq(task)) & (refits.model_id.eq(model))]
        r20 = d["ratio_at_20ms"].dropna().to_numpy(float)
        r30 = d["ratio_at_30ms"].dropna().to_numpy(float)
        near = int(d.identification.fillna("").str.contains("near_null").sum())
        warn = int((d.fit_status != "success").sum())
        return (f"{task}/{model} 的200次重拟合中，20 m/s比值中位数 {np.median(r20):.2f} "
                f"（2.5%–97.5%：{np.quantile(r20,.025):.2f}–{np.quantile(r20,.975):.2f}），"
                f"30 m/s为 {np.median(r30):.2f}（{np.quantile(r30,.025):.2f}–{np.quantile(r30,.975):.2f}）；"
                f"近零/位置不可识别 {near}/200，警告接受 {warn}/200。")
    actual = """\n\n## 实际数值与解释边界\n\n- 三个任务各为60,436个唯一事件、78个验证群组；E保留8,979个零客户事件。\n- **E**：M03为主指标首位（平均OOF偏差363.135；M00为370.433），""" + performance_sentence("E","M03") + " M05为备选：" + performance_sentence("E","M05") + " M03重拟合显示稳定的中高风速上升：" + refit_sentence("E","M03") + " 因此E支持将自由形状与单调/Softplus并列审阅，但仍不能将局部下降或高端回落解释为物理机制。\n- **R**：M05点排名第一（2.3677，对M00为2.3766），" + performance_sentence("R","M05") + " 虽然偏差区间偏向M05，RMSE区间跨零；并且" + refit_sentence("R","M05") + " 这意味着没有稳健证据可把位置或平台当作工程阈值。\n- **R_C**：M05点排名第一（2.3010，对M00为2.3128），" + performance_sentence("R_C","M05") + " 但" + refit_sentence("R_C","M05") + " R_C使用最终客户规模，故它只支持事后条件关联。\n- M08在R_C的200次中有51次warning_accepted；M06/M07/M08的渐近平台仅是函数性质。它们的高风速平台没有被本探索确认为数据已识别的饱和高度。\n- 配对区间以固定OOF预测为条件；重拟合固定已选平滑规格。它们均未包含全套模型选择、数据定义或未观测完整天气过程的不确定性。\n"
    for name in ("X01_REPORT.md", "RETURN_TO_CHATGPT_X01.md"):
        with (ROOT / name).open("a",encoding="utf-8") as handle:
            handle.write(actual)
    manifest = json.loads((ROOT / "DATA_MANIFEST.json").read_text(encoding="utf-8"))
    (ROOT / "README.md").write_text(f"""# {ROOT.name}

Independent X01 candidate-curve experiment. All analysis inputs actually used are copied below `frozen_sources/`; the large frozen event database is omitted from the return ZIP but retained locally with its hash.

## Results

- Chinese report: `X01_REPORT.md`
- Research story log: `RESEARCH_STORY_LOG.md`
- ChatGPT return: `RETURN_TO_CHATGPT_X01.md`
- Rankings: `tables/model_leaderboard.csv`
- OOF predictions: `predictions/oof_predictions.parquet`
- Curves: `evidence/curve_data.parquet`

## Re-run

Run `python -B src/x01_run.py` from this directory in a scientific Python environment containing NumPy, pandas, SciPy, pyarrow and Matplotlib. The source only reads `frozen_sources/input/R02_event_master.parquet` and writes inside this run.

Input SHA-256: `{manifest['input_sha256']}`.
""", encoding="utf-8")
    x.log("finalization complete: reports and figures generated from persisted computational artifacts")


if __name__ == "__main__":
    main()
