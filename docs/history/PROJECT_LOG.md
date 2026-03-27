# 项目日志（归档整理版）

## 1. 文档性质

本文件是对项目早期推进过程的整理版日志，用于记录关键节点和重要决策。它是历史记录，不是当前仓库状态说明。

## 2. 关键里程碑

### 2026-03-20

- 明确课程主题聚焦于 `Reliability of LLM Evaluation`
- 确定项目核心问题不只是比较最高准确率，而是分析排名稳定性
- 确认使用多 benchmark、多 prompt 扰动和 bootstrap 子集重采样的总体思路

### 2026-03-21

- 初步确定四阶段流水线结构：
  1. 数据抽样与 prompt 生成
  2. 模型推理
  3. 答案解析与评分
  4. 统计分析与可视化

### 2026-03-23

- 完成 pilot 级别的流程打通
- 验证从 prompt 生成到评分输出的端到端路径可运行
- 记录过一次 prompt 模板调整：不再在所有模板中都强制写死“只返回一个字母”

### 2026-03-24 到 2026-03-25

- 完成 Phase 2 的全量 notebook 运行
- 生成 `02_raw_responses` 系列文件
- 完成评分脚本与 bootstrap 分析脚本
- 产出主分析表格、MMLU subject 分析表格、图表和报告草稿

### 2026-03-26 到 2026-03-27

- 对仓库结构进行标准化整理
- 增补架构说明、复现说明和 AGENTS 文档
- 对齐 `02_api_runner.py` 与 notebook 的真实运行口径
- 新增统一入口 `run_pipeline.py`

## 3. 关键决策

### 决策 1：关注 ranking stability，而不只看 average accuracy

原因：

- 课程主题强调评测可靠性；
- 单一 leaderboard 无法体现 prompt 扰动与样本波动下的排名不确定性。

### 决策 2：使用 bootstrap，而不是只报告单次测试集结果

原因：

- bootstrap 可以显式量化置信区间；
- 可以分析 ranking reversal rate 和 rank probability。

### 决策 3：最终报告以真实运行结果为准，而不是以早期计划为准

原因：

- 早期计划中的模型与后续真实运行模型不完全一致；
- 当前仓库已经有完整产物，必须优先服从真实结果。

## 4. 当前阅读建议

如果你想了解当前仓库，而不是回顾历史推进过程，请优先阅读：

1. [README.md](/d:/ST5230/LLM-Ranking-Reversals/README.md)
2. [ARCHITECTURE.md](/d:/ST5230/LLM-Ranking-Reversals/docs/ARCHITECTURE.md)
3. [REPRODUCIBILITY.md](/d:/ST5230/LLM-Ranking-Reversals/docs/REPRODUCIBILITY.md)
