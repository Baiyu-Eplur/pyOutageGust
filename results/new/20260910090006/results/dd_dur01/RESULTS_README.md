# DD-DUR01 运行与结果字段说明

生成：2026-09-10T09:04:06.644077+01:00。运行结果：`D:/Pyprogramme/pyOutageGust/results/new/20260910090006/results/dd_dur01`。

本文件仅说明实现、字段、复现方法及技术状态，不作独立科学审查或主模型采用判断。

## 实际运行方式

当前环境执行命令：`C:/Users/haoya/.conda/envs/pyoutagegust/python.exe -X utf8 -B -c "import main_new; main_new.STEPS['dd_dur01']=1; main_new.main()"`。

常规独立运行：在项目根目录 main_new.py 将最后的 `STEPS['dd_dur01']` 改为1，其余研究阶段保持0，运行 `python -X utf8 -B main_new.py`。只依赖普通Python程序和本地文件，无agent、LLM或对话单元依赖。默认交付的阶段开关仍为0。无需开启DD-AGG01或P03阶段、无需REUSE_RUN。基准/天气运行号分别在DD_DUR01_BASE_RUN和DD_DUR01_WEATHER_RUN设置；只读校验后复用。每次输出新的秒级目录，不覆盖旧运行。

## 固定定义与文件

- protocol.json / PROTOCOL.md：冻结输入指纹、单位、范围、模型、优化/评价/图形规则、源码与环境版本。
- thresholds.csv：scope=full或fold_0..4；tau为该训练范围全部LAD小时阵风的linear90%分位，单位m/s；training_hours按LAD小时等权（共享网格不去重），training_lads与held_out_fold可追踪。
- features_by_fold.csv.gz：六个scope各包含完整121,656行；role=train/test或full，fold为原LAD折号。G单位m/s；H为严格g>tau的小时数，h=H/24；I为sum(max(g²−tau²,0))，单位(m/s)²·小时；J=I/(24tau²)，x=log1p(J)无量纲。模型使用h或x，不额外标准化/中心化。full表仅供描述，不进入OOF。
- feature_support.csv：各训练/测试范围，全部G及固定5m/s箱内的H/I/h/J/x/G分布、零/正值数、相关；空箱n=0且统计NaN，不删除。joint_support_bins.csv及观察支持图只展示已有天气组合，不创建G>tau且H=0的预测情景。
- baseline_match.json：与DD-AGG01有效A01的数据、标签、折号、范围、全部48项NLL/参数预测和BS匹配。M0复用48项，不新增重拟合。
- fit_summary.csv / parameters.csv：144目标；candidate=M0/M1/M2，scope全样本或训练折；M1/M2各重新估计theta/beta/p0/gamma，M0 gamma=0。origin标识复用或新拟合；valid是数值检查，weak_identification与theta_outside_support另列，不能等同采用结论。所有参数和gamma正负照实保留。
- optimizer_candidates.csv.gz：M0原诊断导入，M1/M2各16初值及全部优化终点、状态/梯度/边界/离散度/选择原因；同范围M0 gamma=0是合法候选。baseline_nll与nll_gain_vs_m0仅为拟合诊断。gamma物理范围[-20,20]；仅优化坐标用训练特征RMS缩放，回存物理gamma。
- oof_predictions.csv.gz：原键、fold、8标签，训练折tau及G/H/I/h/J/x；每任务 `target__M0/M1/M2` 为折外概率，`target_constant` 为训练标签事件率。没有使用full参数或full阈值。full_predictions.csv.gz仅保存观察到组合的全样本描述预测，不用于评分或校准。
- metrics.csv / fold_metrics.csv：逐行池化BS、M0基准、绝对/相对下降、训练常数BSS；positive gain表示BS降低。valid_cv/valid=false时正式BS/增量/BSS为NaN，diagnostic_brier可保留算法输出但不能用作有效比较，不删坏折重算。
- paired_uncertainty.csv：M1/M2相对M0的1000次整LAD配对固定OOF条件区间，三模型同抽样、同种子、保留行数权重。不覆盖重训、模型选择、阈值重新估计及共享风暴/日期的全部不确定性。
- calibration_bins.csv / calibration_edges.json：本轮M0/M1/M2有效OOF概率共同十分位边界，补0/1去重，searchsorted(right)，n<100稀疏标记、空箱NaN，不改箱或删尾部。它与DD-AGG01候选集合不同，不能将两轮校准RMSE直接当同比进步。CSV须 `float_precision='round_trip'` 回读。
- figures：每任务全范围+主要支持区间放大校准图，范围外尾部数注明且全图保留；无效模型在图例注明；观察联合支持图无模型胜出标题。figure_axes.json记录显示范围。
- validation.json / execution.jsonl / inventory.json：必要实现核验、逐目标执行状态、输入/产物指纹。invalid/error如存在需按目标定位，不能静默填常数；程序completed表示文件流程完成，不代表每项拟合有效或科学采用。

## 技术完成范围

144个目标记录：48个M0复用，96个M1/M2新增。有效144，无效0，弱识别标记0。本轮必要核验205项，全部通过=True。具体无效、边界或超观察支持记录见参数表，不在此给科学裁决。

tau是数据尺度参考；H是小时阵风指标超过阈值的小时计数；J混合超阈强度与持续性，不是纯时长、损伤或能量测量。gamma可正可负，不能把负系数直接解释为保护机制。固定持续性值下数学中点为theta exp(−beta gamma feature)，概率(1+p0)/2，不能无视联合支持当作一般50%物理阈值。没有增加时间验证、天气源、M3、其他阈值/幂次。未改论文、未生成回传包；本轮在技术结果交付处停止。
