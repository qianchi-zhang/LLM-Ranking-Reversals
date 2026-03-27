# AGENTS.md

## 1. 文件目的

本文件用于约束后续 agent 在本仓库中的工作方式，目标是：

- 保持项目结构清晰；
- 保持数据契约稳定；
- 保持文档与真实实现一致；
- 不破坏已有实验产物。

如果历史文档、README 和实际代码不一致，默认以 `develop` 分支中的当前脚本、数据产物和 `docs/` 标准说明为准。

## 2. 仓库定位

这个仓库不是课程作业模板，而是一个已经完成主实验并产出分析结果的项目仓库。后续 agent 的默认任务应当是：

- 维护和增强现有流水线；
- 修正文档与实现之间的偏差；
- 在不破坏既有产物的前提下做增量改进。

## 3. 目录语义

- `run_pipeline.py`：统一入口，负责串联 Phase 1 到 Phase 4。
- `src/`：标准实验脚本。
- `src/legacy/`：归档的历史脚本，不属于默认复现入口。
- `data/`：数据和表格结果。
- `plots/`：最终图表。
- `reports/`：分析型文字产物。
- `docs/`：架构、复现和标准化说明。
- `docs/history/`：历史计划、日志、技术记录。
- `docs/archive/`：proposal、feedback 等归档材料。

## 4. 当前标准流水线

### Phase 1

- 入口：`src/01_data_prep.py`
- 输出：`data/00_raw_question.jsonl`、`data/01_prompts.jsonl`

### Phase 2

- 入口：`src/02_api_runner.py`
- 历史 notebook：`src/02_api_runner.ipynb`
- 输出：`data/02_raw_responses.jsonl`、`data/02_raw_responses.csv`

### Phase 3

- 入口：`src/03_scorer.py`
- 输出：`data/03_scored/`

### Phase 4

- 入口：`src/04_analysis.py`、`src/04_mmlu_subject_bootstrap.py`
- 输出：`data/04_analysis/`、`data/04_mmlu_subject_analysis/`、`plots/`、`reports/`

### 统一入口

- 推荐入口：`python run_pipeline.py`
- 默认用途：串联完整流水线
- 部分重跑：通过 `--start-phase` 和 `--end-phase` 控制

## 5. 当前实验口径

### 数据规模

- 原始题目：900
- Prompt requests：3600
- 模型结果：14400

### Prompt 模板

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

### 实际模型集合

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

说明：

- 历史计划里曾出现 Claude；
- 当前真实实现和产物不使用 Claude；
- 讨论、README 和复现说明都应以当前真实模型集合为准。

## 6. 数据契约

后续修改若涉及上下游字段，必须同步检查整条流水线。关键字段包括：

- `item_id`
- `request_id`
- `dataset`
- `subject`
- `split`
- `template_name`
- `messages`
- `metadata`
- `model_id`
- `raw_response`
- `gold_answer`
- `parsed_answer`
- `score`

## 7. 修改原则

### 7.1 默认不覆盖已有产物

以下内容默认视为已完成实验产物：

- `data/01_prompts.jsonl`
- `data/02_raw_responses.*`
- `data/03_scored/*`
- `data/04_analysis/*`
- `data/04_mmlu_subject_analysis/*`
- `plots/*`
- `reports/*`

除非用户明确要求重跑，否则不要随意覆盖。

### 7.2 优先做标准化补强

优先事项：

- 修复文档与实现不一致；
- 增补复现入口和复现实验说明；
- 保持 `run_pipeline.py` 与分阶段脚本一致；
- 对齐 notebook 历史口径与脚本口径。

避免事项：

- 无必要地大规模重构目录；
- 改写已稳定的数据产物路径；
- 在未确认影响范围时修改数据 schema。

### 7.3 历史文档视为参考

`docs/history/` 和 `docs/archive/` 的内容可用于追溯背景，但不是最终事实来源。只要与当前实现冲突，应以当前代码和产物为准。

## 8. 安全规则

- 不打印或回传 `OPENROUTER_API_KEY`。
- 不主动修改 `my.env` 或 `.env`。
- 不把凭证写入新的文档、日志或报告。

## 9. 推荐工作顺序

如果用户要求继续完善项目，默认优先级如下：

1. 保证 [README.md](/d:/ST5230/LLM-Ranking-Reversals/README.md) 与真实结构一致。
2. 保证 [REPRODUCIBILITY.md](/d:/ST5230/LLM-Ranking-Reversals/docs/REPRODUCIBILITY.md) 与当前入口一致。
3. 保证 `run_pipeline.py`、`src/02_api_runner.py` 和主分析脚本口径一致。
4. 在不破坏既有结果的前提下再扩展分析。

## 10. 一句话原则

把这个仓库当作“已经有真实实验产物、需要继续标准化和增强可复现性”的项目来维护，而不是当作一个尚未实现的空模板。
