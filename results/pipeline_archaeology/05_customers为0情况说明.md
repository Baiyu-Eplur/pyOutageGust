# Step 5：customers = 0 情况说明

## 结论（先给结论）

**整条九步主链中，没有任何脚本对 `Number of Customers Restored` / `customers_restored` 做过针对"=0"这个取值的特殊处理（既没有过滤掉，也没有单独标记或替换）。凡是数据集中出现的 customers=0 记录，都是原始字段本身自然带出来的值，是 `filter.py` dedup 后幸存的那一条 Restoration Stage 记录里 `Number of Customers Restored` 字段原始就是 0（或缺失后被当作数值 0 处理），并非任何后续代码逻辑主动产生或允许通过的。**

## 逐脚本核实过程（如实记录）

沿用 `03_脚本详细文档.md` 中对全部 12 个主链+子链脚本的精确代码摘录结果，专门检索是否存在任何形如 `customers == 0`、`customers > 0`、`.dropna(subset=["Number of Customers Restored"...])`、`fillna` 针对该字段、或任何以 0 为阈值的过滤条件：

- **`filter.py`**：`generate_weather_fetch_list_strict()` 及 `classify_cause_code()`/`normalize_cause_code()` 三个核心函数中，过滤/筛选逻辑**只围绕 Cause Code**（`keep_groups = {"weather_natural", "technical_asset"}` 及 dedup 的 `drop_duplicates(subset=[incident_col], keep="first")`），全文未出现任何针对 `Number of Customers Restored` 字段数值的判断、过滤或填充语句。
- **`main1.py`**：核实到的行级过滤逻辑只有 `df = df.dropna(subset=["clean_start", "lat", "lon"]).copy()`（第545行附近，导致行数从 66,080 降到 62,928），过滤条件是**时间解析失败或坐标缺失**，与 customers 数值无关。
- **`match_lad.py`、`poppulation_merge.py`、`Buckinghamshire_combination.py`、`GVA_merge_with_crosswalk.py`、`LAD_GeoMerge.py`**：均为按 LAD 代码/坐标做的左连接（`sjoin`/`merge`），不涉及对 customers 字段的任何判断。
- **`data_arrange.py`**：只计算 `Duration (hours)`/`Daytime Indicator`/`Hour`/`Month`/`Weekday` 五个新列，未触碰 customers 字段。
- **`deeprig.py`**（建模脚本，不属于九步主链，但因是唯一出现 "Customer" 关键字的脚本而额外核实）：第101行 `df["customers_restored"] = safe_num(df["Number of Customers Restored"])`——`safe_num` 是通用数值类型转换函数（在同一脚本中定义，用于处理字符串数字、千分位逗号等格式问题），**不包含任何针对 0 值的特殊分支**，0 会被正常转换并保留为 0，不会被转成 NA 或被过滤掉。

## Cause Code 是否间接导致 customers=0（附带核实，非另开新调查）

按命令要求，"除非 Step 3 代码逻辑本身用 Cause Code 做过滤才顺带记录"——`filter.py` 确实用 Cause Code 做了记录级过滤（只保留 `weather_natural`/`technical_asset` 两组），但这个过滤发生在 **incident 级别（是否保留整个事故记录）**，与"该事故的 Number of Customers Restored 数值是多少"是两件独立的事——一条记录只要 Cause Code 落在保留组内就会被保留，不论其 customers 数值是多少（包括0）。因此 Cause Code 筛选**不是**customers=0 记录存在的原因,它只决定"哪些事故进入分析",不决定"进入分析的事故 customers 取值"。

## 对 customers=0 成因的推测（明确标注为推测,非代码证据)

虽然代码层面没有任何"制造"customers=0 的逻辑,但 customers=0 在原始 IIS 申报数据中自然存在是可以理解的——例如:某次抢修事件的最早一条 Restoration Stage 记录可能对应"计划检修但尚未有客户实际断电被记录"或"数据申报时该字段留空后被当作0处理"等情况。**这一段是基于对停电数据业务常识的合理推测,不是从本命令已核实的代码或文档中找到的直接证据**,如需确认真实成因,需要直接查看原始 `ukpn-iis.csv` 中 customers=0 记录对应的其他字段(如 Cause Code、Restoration Stage 标记、是否为计划性中断等),而原始文件本次未能传输到沙箱,本命令未做这一步验证,如实记录为未验证事项。

## 与 customers/duration 计算逻辑缺陷的关系

Step 4 已确认 customers 是"该 incident 最早一条 Restoration Stage 记录的原始值透传"。如果按官方口径正确聚合多阶段记录后,原本某些 customers=0 的记录有可能因为该 incident 其他被丢弃的阶段记录中包含非零客户数而被重新计算为非零值——但这只是基于 Step 4 结论的逻辑推论,本命令未直接验证,列为 Step 6 综合结论里需要在未来重新计算 customers 时一并核查的问题(即:重算后 customers=0 的记录数量和具体是哪些 incident,是否与当前不同,需要用聚合后的新逻辑重新统计)。
