# Step 1：构造naive/legacy式customers与duration

## 复用命令#9样本与折

调用命令#9脚本（`v3_validation_pipeline.py`）的Step0-2函数原样重跑，得到与命令#9完全相同的样本与折分配：121,313个天气匹配事件 → 完备协变量筛选后117,298个事件，5折`GroupKFold`（分组=incident_date_utc）折分配。因这些函数是确定性计算（无随机种子依赖，`GroupKFold`不做shuffle），重跑结果与命令#9原始运行**逐行一致**，不引入任何新的样本筛选差异，满足验收标准要求。

## naive customers/duration 构造逻辑（严格复用旧filter.py逻辑）

直接核实了 `D:\Pyprogramme\STST2603\filter.py`（用户主线原始脚本，只读）的确切去重逻辑：

```python
df_filtered = df_filtered.sort_values([incident_col, "_sort_time"], kind="stable")
df_unique = df_filtered.drop_duplicates(subset=[incident_col], keep="first")
```

其中 `_sort_time` = `Start Date and Time` 解析后的时间戳。即：**按Incident Reference分组，按Start Date and Time排序（稳定排序），保留每组时间最早的一条Restoration Stage记录**。

本步骤对v3阶段级数据集（`ukpn_full_stage_dataset_v3.csv`）执行完全相同的排序+去重操作（未引入任何新处理规则），得到：
- `customers_naive` = 最早阶段的 `Number of Customers Restored` 原始值
- `duration_naive` = 最早阶段自身的起止时长（即该阶段的 `stage_duration_hours`）

未做Cause Code筛选（与命令#9的样本口径一致，本步骤只隔离"customers/duration定义"这一个变量，不重新引入Cause Code范围差异）。

## 构造结果

对117,298个目标事件（命令#9的完备协变量样本），naive变量**100%可计算**（117,298/117,298 customers_naive非空、117,298/117,298 duration_naive非空）——这是预期之内的，因为naive口径只依赖单一阶段的原始记录，不存在customers_v2/duration_A那样"排除重复中断阶段导致部分事件无法计算"或"加权分母为0"的问题。
