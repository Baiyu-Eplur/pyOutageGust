# 工作命令 #54：构建隔离的主回归模型审查包（供导师检查）

**审查包已构建完成，位于`D:\Pyprogramme\STST2603\STST2603_model_review_package\`（与`claude_branch/`平级，独立顶层目录），已通过全部关键验证。本命令验证过程中发现一处严重问题，须在发送给导师前处理，详见下方"⚠️关键发现"。**

---

## ⚠️关键发现（必须优先处理，发给导师前请先修正论文正文）

**核实确认：论文正文当前的"Table 2"（阵风系数表）显示的仍是C01修复前的旧数字，不是C01+C02-C08修复后的最终数字。**

论文`Paper1_draft.md`第156-161行当前显示：

| | Exposure margin | Recovery margin |
|---|---|---|
| Gust (linear) | -0.032 (p = 0.022) | 0.000 (p = 0.982) |
| Gust squared | 0.103 (p < 0.001) | 0.079 (p < 0.001) |

而本命令独立运行验证得到的（同时也是命令#45-53全程反复引用、写入Appendix F、Figure 4/10的）真实最终数字是：

| | Exposure margin | Recovery margin |
|---|---|---|
| Gust (linear) | **-0.036014** (p=0.009958) | **-0.000993** (p=0.913032) |
| Gust squared | **0.105997** (p=6.08×10⁻³⁷) | **0.084954** (p=1.01×10⁻⁴³) |

**这不是巧合或四舍五入误差**——核对LOG.md确认，Table 2当前显示的数字（含p值0.022、0.982）与命令#44/#46记录的**C01修复前**基线数字精确吻合（"log-OLS基准（一次项-0.0323 p=0.022，二次项+0.1028 p=9.3e-31）...log-OLS基准（一次项+0.0002 p=0.982不显著，二次项+0.0792...）"）。也就是说：**从命令#44修复C01开始到现在的整条修复链路（命令#44-53）里，论文正文Table 2这张表本身的四个数字和两个p值从未被实际更新过**，尽管Appendix F、Figure 4/10、临界风速等几乎所有其他相关数字都已经过多轮核实同步。

**如果现在就把审查包发给导师**，导师会发现审查包独立跑出来的系数（-0.036/0.106等）与论文正文Table 2（-0.032/0.103等）对不上——这正是命令#54反复强调的"任何数字不一致都会比论文本身的小错误更严重地影响可信度"这一最坏情况。**强烈建议在发送审查包之前，先把Table 2的四个系数和两个p值更新为上表右侧的修正后数字。**

（审查包本身没有问题——它独立验证后完全匹配命令#45存档的原始结果，见下方Step 5。这是论文正文本身遗留的同步缺口，不是审查包的缺陷。）

---

## Step 1：确认"主回归模型"的确切文件清单

**E0/R0c共用的核心拟合逻辑**分布在三个文件中（历史上因增量修复采用猴子补丁架构，未合并为单一脚本）：

1. `claude_branch/scripts/v3_validation/v3_validation_pipeline.py`——`design_train_valid()`函数（第191-229行）：标准化+设计矩阵构造，含Table 2/Appendix F列出的全部协变量。
2. `claude_branch/scripts/critical_wind_speed/critical_wind_speed_pipeline.py`——`fit_full_sample()`函数（第119-136行）：调用上述设计矩阵函数、拟合OLS、计算LAD单向聚类稳健标准误。
3. `claude_branch/scripts/c02_c08_repair_20260905/final_core_tables.py`——第74-98行"Combined sample: LAD single + two-way cluster"代码块：在**C01+C02-C08修正后最终合并样本**上调用上述两个函数，额外计算LAD×date双向聚类标准误，产出`E0_corrected_lad_cluster.csv`/`E0_corrected_twoway_cluster.csv`/`R0c_corrected_lad_cluster.csv`/`R0c_corrected_twoway_cluster.csv`——**这四个文件就是Appendix F完整系数表、Table 2（阵风项）、临界风速计算的直接数字来源**。

**判定依据**：这是命令#45（C02-C08修复链路收尾）产出、并被命令#46、#48、#50、#51、#53全部反复引用核对的版本；命令#46核实VIF、命令#48核实bootstrap、命令#51核实development sample行时，全部以这四个CSV为基准数字，确认是当前生效的最终版本，不是任何更早期版本。

**最终分析样本**：`final_core_tables.py`内部通过`corrected_sample_builder.build_corrected_combined_samples()`（命令#44/#45建立的C01修正注入机制）构建，等价于两个DataFrame——`combined_e0`（n=60,437）、`combined_r0cb`（n=59,834）。这两个DataFrame本身从未被缓存为静态文件（历史上一直是每次运行时现算），本命令Step 2专门把它们物化为静态CSV纳入审查包。

## Step 2-3：复制与路径调整

审查包目录结构：

```
STST2603_model_review_package/
├── README.md（英文，供导师直接阅读）
├── requirements.txt
├── data/
│   ├── combined_E0_final.csv（60,437行，25列）
│   └── combined_R0c_final.csv（59,834行，26列）
├── code/
│   ├── run_main_regression.py
│   └── PROVENANCE.md（Step 4的完整diff证据）
└── results/
    ├── E0_corrected_lad_cluster.csv / E0_corrected_twoway_cluster.csv
    ├── R0c_corrected_lad_cluster.csv / R0c_corrected_twoway_cluster.csv
    ├── run_summary.json
    └── verification_report.md（Step 5的完整数字比对）
```

`run_main_regression.py`把上述三个文件中的核心计算函数（`design_train_valid`、`fit_full_sample`的OLS+聚类逻辑、`coef_table`、主拟合代码块）**逐字复制**进同一个文件，唯一的必要改动：不再通过`v9.`/`v11.`模块前缀调用（因为函数现在定义在同一文件内，不再是分散在三个独立模块里靠猴子补丁串联），以及数据来源从"调用完整重建流水线现算"改为"读取本包`data/`下已物化好的最终样本CSV"（命令#54第0.3条明确允许这一简化，不需要打包整条从原始数据到最终样本的重建链路）。**协变量清单、标准化公式、聚类方式、模型设定，逐字未改动一处。**

## Step 4：差异校验（程序化diff，非人工目测）

**未采用"人工数行数、凭印象说只改了路径"的做法**，而是用Python `inspect.getsource()`直接从原始模块提取函数源码、用`difflib.unified_diff`做程序化逐行比对，完整过程和输出见`code/PROVENANCE.md`。结果：

| 比对对象 | 结果 |
|---|---|
| `design_train_valid()` | **完全逐字相同，0行差异** |
| `coef_table()` | **完全逐字相同，0行差异** |
| `fit_full_sample()` | 仅2处差异：删除一段3行的解释性注释（纯文档，无计算影响）；`v9.design_train_valid(...)`→`design_train_valid(...)`（同一函数，仅去掉模块前缀，因为该函数现在定义在同一文件内） |
| 主拟合代码块（design matrix→OLS→LAD/双向聚类） | 仅2类差异：同上的`v11.fit_full_sample(...)`前缀去除；输出路径从原项目的`raw/`文件夹改为本包自己的`results/`文件夹（文件名本身完全一致） |

**结论：diff中出现的每一处差异都只涉及模块引用前缀（因代码合并到单文件而产生的必要调整）和输出路径本身，未发现任何协变量、标准化方式、参数或计算逻辑层面的改动。**

## Step 5：独立运行验证（关键）

**做了两轮验证**：

1. **在本机审查包目录内独立运行**：读取`data/`下的静态CSV，产出四张系数表，与命令#45存档的原始结果（`claude_branch/results/c02_c08_repair_20260905/raw/`下同名四个文件）逐项数字比对，coef/se/p三列共12组比对，**最大绝对差异3.51×10⁻¹³**（浮点噪声量级，远小于命令允许的1e-9容差），完全一致。
2. **完全脱离主项目目录的隔离测试**：把整个审查包复制到系统临时目录（与`D:\Pyprogramme\STST2603\`完全无关的路径），在那里独立运行，产出结果与原始存档结果比对，**最大绝对差异2.96×10⁻¹³**，同样完全一致——证明审查包真正不依赖本机其他文件、可以被复制到任意位置独立运行。

**关键数字对照**（供直接核对）：

| 数字 | 独立运行结果 | 存档原始结果 |
|---|---|---|
| E0样本量 | 60,437 | 60,437 |
| R0c样本量 | 59,834 | 59,834 |
| E0阵风一次项(LAD聚类) | -0.036014 (p=0.009958) | 完全一致 |
| E0阵风二次项(LAD聚类) | 0.105997 (p=6.08e-37) | 完全一致 |
| R0c阵风一次项(LAD聚类) | -0.000993 (p=0.913032) | 完全一致 |
| R0c阵风二次项(LAD聚类) | 0.084954 (p=1.01e-43) | 完全一致 |
| E0临界风速 | 10.8072 m/s | 完全一致 |

**没有发现Step 5要求核查的"独立运行结果与论文数字对不上"这类情况——但正如上方"关键发现"所述，独立运行结果与论文正文Table 2现有显示数字确实对不上，原因是Table 2本身尚未同步更新，不是本审查包的计算有误。**

## Step 6：依赖环境记录

Python 3.12.6；pandas 3.0.1；numpy 2.4.3；scipy 1.17.1；statsmodels 0.14.6。已写入`requirements.txt`。

## Step 7：README撰写

已用英文撰写`README.md`，包含：本包对应的修复链路版本说明、目录结构、运行方法、供导师直接核对的关键数字（Table 2风格的系数表+临界风速）、以及基于Step 4/5证据的"未做任何计算逻辑修改"明确声明，并在README中同样醒目地提示了上述Table 2同步缺口这一注意事项。

## 打包验证

已实测`Compress-Archive`把整个审查包压缩为zip（约8.3MB，含两个约19MB的CSV压缩后），解压后目录结构完整——确认可以正常打包发送。测试压缩包已清理，未保留在项目目录中。

---

## 验收标准逐项确认

- Step 4的diff结果已逐项给出具体diff内容（程序化生成，非笼统断言"只改了路径"），并对每一处非路径字符串本身的差异（模块前缀去除）给出了具体解释。
- Step 5的独立运行结果已与存档原始结果逐项数字比对，两轮验证（本机+完全隔离环境）均确认完全一致（1e-13量级浮点噪声内）。
- 审查包已实测可被完整打包为zip、脱离项目目录后独立解压运行，产出与存档结果一致。
- README已用英文撰写，包含目录结构、运行命令、供直接核对的具体数字、及未做计算逻辑修改的明确声明。
- **按提醒要求，未掩盖或忽略"Step5独立运行结果与论文已发布数字对不上"这一实际发现**——已在报告开头、`verification_report.md`、`README.md`三处均醒目披露"论文正文Table 2尚未同步更新至C01+C02-C08修正后数值"这一严重问题，并给出具体的修正数字供直接替换。

## 产出文件

审查包本体：`D:\Pyprogramme\STST2603\STST2603_model_review_package\`（独立顶层目录，与`claude_branch/`平级）。本命令过程性文件：`claude_branch/scripts/model_review_package_20260907/materialize_final_data.py`（一次性物化最终数据集用，不属于审查包本身）。
