# R05-5 最终消费者复现

最终单入口（已实际运行；工作目录项目根）：

```powershell
& .\paper_revision_work_v2\R03\runtime\python\python.exe -I -S -B .\paper_revision_work_v2\R05\cli.py consumers
```

该入口在新发布目录不存在时执行完整12图渲染；存在时验证24个图件和全部冻结输入SHA后复用，再逐值审计并发布246个当前语义绑定。实际执行记录见logs/consumers.txt、checks/consumer_single_entry.json，图件与绑定各有当前指针。下列为同一入口内部步骤的审计命令：

```powershell
& .\paper_revision_work_v2\R03\runtime\python\python.exe -I -S -B .\paper_revision_work_v2\R05\cli.py render_release
& .\paper_revision_work_v2\R03\runtime\python\python.exe -I -S -B .\paper_revision_work_v2\R05\cli.py writing
```

12组图PNG/PDF已实际生成在R05/release_v1/figures；日志logs/render_release.txt，检查checks/consumer_reproduction.json。入口使用复制后的R04代码的明确绘图段：初始11→最终02/03/D1/F1→最终05/08→D1数值bin复核。截断点记录于CONSUMER_INPUTS.json；没有执行原代码拟合/全数据生产段。当前入口拒绝覆盖已存在release_v1；如需再次完整渲染应在派生副本中指定新发布目录并更新经审查的指针，不能单跑旧renderer充当新发布。

图件当前身份在CURRENT_CONSUMER_RELEASE.json；源表快照位于release_v1/tables。语义绑定由writing命令逐值核查后发布到R05/tables/CURRENT_NUMERIC_BINDINGS_R05.csv、CURRENT_PARAGRAPH_BINDINGS_R05.csv及NUMERIC_BINDING_SEMANTIC_AUDIT.csv；旧表快照不是修正标签的权威。A-T10的10处six-group标签已纠正，数值未变。

所有图消费相同冻结数组与参考定义；计数为整数精确比较，浮点预测/表值容差1e-12（协方差参考对照因不同线代路径用显式atol/rtol）。6个PNG与R04逐像素/字节相同；其余PNG因统一rcParams/布局执行顺序有差异，PDF元数据/版式不要求字节相同，不能把非同SHA归咎于仅时间戳。FIGURE_RELEASE_COMPARISON.csv逐文件区分字节身份和数据一致。

已查看12图总览及D1单图，检查改变过的02/03/05/08/D1面板、图4四组与图10无区间；图1经纬度hexbin无许可边界和inset；图6地图有效范围；F1残差重尾明显。属于科学内容与可读性验收，不是最终期刊排版。图3密集窗口标签在总览较小，单图保留可放大。

图4/6为exp(meanη)/exp(weighted meanη)，不等于mean(expη)或算术客户/小时均值。E对应1+C，未减1。图7为50点p1–p99网格max/min；图9两种预测身份、唯一4452事件及对数目标明确；图10单full分期点；D1各总体自己的数值bins，主/天气pooled均递减。图1的计数/坐标/边界缺项进入候选图注。运行标签保留供审阅，最终稿实现标签可移至复现说明。

| figure | format | bytes | byte_identical_to_R04 | pixel_equal |
| --- | --- | --- | --- | --- |
| figure01 | png | 182350 | True | True |
| figure01 | pdf | 21625 | False | 未定义/不适用 |
| figure02 | png | 113364 | False | False |
| figure02 | pdf | 21432 | False | 未定义/不适用 |
| figure03 | png | 72263 | False | False |
| figure03 | pdf | 15406 | False | 未定义/不适用 |
| figure04 | png | 147242 | True | True |
| figure04 | pdf | 17731 | False | 未定义/不适用 |
| figure05 | png | 62863 | False | False |
| figure05 | pdf | 14881 | False | 未定义/不适用 |
| figure06 | png | 340858 | True | True |
| figure06 | pdf | 1460735 | False | 未定义/不适用 |
| figure07 | png | 56541 | True | True |
| figure07 | pdf | 13250 | False | 未定义/不适用 |
| figure08 | png | 63919 | False | False |
| figure08 | pdf | 15150 | False | 未定义/不适用 |
| figure09 | png | 447626 | True | True |
| figure09 | pdf | 37482 | False | 未定义/不适用 |
| figure10 | png | 107476 | True | True |
| figure10 | pdf | 16501 | False | 未定义/不适用 |
| figureD1 | png | 257831 | False | False |
| figureD1 | pdf | 19367 | False | 未定义/不适用 |
| figureF1 | png | 329050 | False | False |
| figureF1 | pdf | 1153538 | False | 未定义/不适用 |

数字覆盖：950原槽位（含历史/引用/公式），246绑定逐值语义复核，90处候选位置，963行迁移表。11组合段落逐段候选；Word未修改；OCR与所有公式对象仍属W最终核查范围。
