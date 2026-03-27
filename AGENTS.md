# AGENTS.md

## 1. 文件目的

本文件用于告诉后续 agent：这个仓库当前到底长什么样、哪份代码和数据是真实落地的、哪些文档已经过时，以及修改时必须遵守哪些边界。

如果文档、README、计划书和实际代码不一致，默认以 `develop` 分支中的实际文件与已生成产物为准。

## 2. 当前基准分支

当前应以 `develop` 分支作为项目最新主工作线。

后续 agent 在开始工作前，默认先确认：

- 当前是否位于 `develop`
- 工作区是否有未提交改动
- 本地脚本、数据产物、报告和图表是否与任务相关

不要先凭 README 想象目录结构，再去套模板改仓库。

## 3. 当前实际项目架构

截至当前 `develop` 分支，仓库里的主要结构是：

```text
LLM-Ranking-Reversals/
├─ src/
│  ├─ 01_data_prep.py
│  ├─ 02_api_runner.py
│  ├─ 02_api_runner.ipynb
│  ├─ 03_scorer.py
│  ├─ 04_analysis.py
│  └─ 04_mmlu_subject_bootstrap.py
├─ data/
│  ├─ 00_raw_question.jsonl
│  ├─ 01_prompts.jsonl
│  ├─ 02_raw_responses.jsonl
│  ├─ 02_raw_responses.csv
│  ├─ 03_scored/
│  │  ├─ scored_results.csv
│  │  └─ parse_failures.csv
│  ├─ 04_analysis/
│  │  ├─ accuracy_by_dataset_model.csv
│  │  ├─ accuracy_by_dataset_model_prompt.csv
│  │  ├─ bootstrap_accuracy_long.csv
│  │  ├─ pairwise_significance.csv
│  │  ├─ rank_probability.csv
│  │  └─ ranking_reversal_rate.csv
│  └─ 04_mmlu_subject_analysis/
│     ├─ mmlu_scheme_overall_accuracy.csv
│     ├─ mmlu_scheme_pairwise_significance.csv
│     ├─ mmlu_scheme_prompt_accuracy.csv
│     ├─ mmlu_scheme_rrr.csv
│     ├─ mmlu_subject_overall_accuracy.csv
│     ├─ mmlu_subject_pairwise_significance.csv
│     ├─ mmlu_subject_prompt_accuracy.csv
│     └─ mmlu_subject_rrr.csv
├─ plots/
├─ reports/
├─ README.md
├─ PROJECT_PLAN.md
├─ PROJECT_LOG.md
├─ TECH_STACK.md
├─ requirements.txt
├─ my.env
├─ group_14_feedback.txt
├─ ST5230 Group Project Proposal - Group 14.pdf
├─ ST5230_group project.pdf
└─ mxc.py
```

注意：

- 这不是 README 里写的理想化目录树，而是当前仓库真实存在的结构。
- `reports/`、`plots/`、`data/03_scored/`、`data/04_analysis/`、`data/04_mmlu_subject_analysis/` 已经落地。
- 当前 Phase 4 不是 notebook，而是以 `src/04_analysis.py` 和 `src/04_mmlu_subject_bootstrap.py` 两个 Python 脚本为主。

## 4. 四阶段流水线

### Phase 1：数据抽样与 Prompt 生成

主文件：

- `src/01_data_prep.py`

输入来源：

- HuggingFace 数据集 `cais/mmlu`
- HuggingFace 数据集 `allenai/ai2_arc`
- HuggingFace 数据集 `Rowan/hellaswag`

当前抽样设计：

- MMLU：6 个 subject，每个 50 题，共 300 题
- ARC-Challenge：300 题
- HellaSwag：300 题
- 总题量：900

当前 prompt 模板名：

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

输出文件：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

当前已知产物规模：

- `data/00_raw_question.jsonl`：900 条题目
- `data/01_prompts.jsonl`：3600 条 prompt 请求

### Phase 2：OpenRouter 推理

主文件：

- `src/02_api_runner.py`
- `src/02_api_runner.ipynb`

输入文件：

- `data/01_prompts.jsonl`

输出文件：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

当前代码中的实际模型列表是：

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

这点非常重要：

- `PROJECT_PLAN.md` 和部分旧文档里写的是 Claude 3.5 Haiku
- 但当前真实代码和分析报告使用的是 Qwen 2.5 7B，而不是 Claude
- 如果写文档、报告或结论，优先以实际跑出的数据和当前脚本中的模型集合为准

另外一个关键坑：

- 当前 `src/02_api_runner.py` 里仍然保留了 `tasks = all_tasks[:50]`
- 这意味着脚本默认只会跑前 50 个 prompt
- 但仓库里现有 `data/02_raw_responses.csv` 和后续分析产物显然来自完整实验
- 所以“当前脚本”和“当前数据产物”并不是完全一一对应的同一版执行状态

后续 agent 如果要重跑 Phase 2，必须先明确：

- 是只做 pilot run
- 还是要跑 full run

如果是 full run，不能直接沿用这段切片逻辑。

### Phase 3：答案解析与打分

主文件：

- `src/03_scorer.py`

输入文件：

- `data/02_raw_responses.csv`

输出文件：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

核心行为：

- 从 `raw_response` 中提取 A/B/C/D
- 从 `metadata` 中读取 `gold_answer`
- 生成 `parsed_answer`、`parse_method`、`is_parsed`、`score`
- 无法解析的记录不能静默丢弃，必须进入 `parse_failures.csv`

当前已知规模：

- `scored_results.csv` 共 14401 行，含 1 行表头，即 14400 条评分记录
- `parse_failures.csv` 共 4 行，含 1 行表头，即 3 条解析失败记录

### Phase 4：Bootstrap 统计分析

主文件：

- `src/04_analysis.py`

输入文件：

- `data/03_scored/scored_results.csv`

输出目录：

- `data/04_analysis/`
- `plots/`
- `reports/analysis_summary.md`

当前分析内容包括：

- 每个数据集、每个模型的总体准确率
- 每个数据集、每个模型、每个 prompt 的准确率
- bootstrap 95% CI
- pairwise significance
- ranking reversal rate
- rank probability heatmap 所需数据

### Phase 4 补充：MMLU Subject 级分析

主文件：

- `src/04_mmlu_subject_bootstrap.py`

输入文件：

- `data/03_scored/scored_results.csv`

输出目录：

- `data/04_mmlu_subject_analysis/`
- `plots/`
- `reports/mmlu_subject_bootstrap_summary.md`

这部分是针对 MMLU 的进一步细化分析，比较：

- `overall_pooled`
- `overall_stratified`
- `subject_only`

也就是说，后续 agent 不应再把 MMLU 只当成“普通数据集的一部分”，而应意识到这里已经有 subject-aware 的专门分析链路。

## 5. 当前仓库的事实性结论

从现有产物看，这个仓库已经不是“只有计划”的空壳，而是一个已经跑完主体实验、已生成结果和图表的项目仓库。

至少以下事实已经成立：

- 900 条原始题目已生成
- 3600 条 prompt 已生成
- 14400 条模型评分结果已生成
- 主体 bootstrap 分析已落地
- MMLU subject 级 bootstrap 分析已落地
- 报告草稿和图表已经存在于仓库中

因此，后续 agent 的默认工作方式不应是“从零搭架子”，而应是：

- 理解并维护现有流水线
- 在不破坏数据契约的前提下修补或扩展
- 对旧文档进行纠偏

## 6. 文档与代码的已知不一致

当前仓库至少有以下不一致，后续工作必须注意：

### 6.1 README 与真实结构不一致

- README 仍然描述 `docs/`、`utils/`、`04_analysis.ipynb`
- 实际仓库中没有这些对应结构或主文件
- 实际主分析脚本是 `src/04_analysis.py`

### 6.2 计划书与真实模型集合不一致

- 计划书中写过 Claude 3.5 Haiku
- 实际当前代码和分析产物中使用的是 Qwen 2.5 7B

### 6.3 Phase 2 代码与 Phase 2 产物可能不是同一执行版本

- `src/02_api_runner.py` 默认只跑前 50 条任务
- 但当前结果文件是完整规模
- 若要复现实验，必须先统一这件事

### 6.4 若干 markdown 在当前终端中有编码显示问题

- `README.md`
- `PROJECT_PLAN.md`
- `PROJECT_LOG.md`
- `TECH_STACK.md`
- `.gitignore`

这类文件在当前 shell 中可能出现乱码显示。

处理原则：

- 不要把乱码原样复制进新文件
- 新写文档优先直接写干净的中文或 ASCII
- 如果要修复编码，单独作为明确任务处理

## 7. 安全与敏感信息规则

### 7.1 不要泄露密钥

仓库中存在 `my.env`，而当前 `src/02_api_runner.py` 会从这个文件读取 `OPENROUTER_API_KEY`。

后续 agent 必须遵守：

- 不打印 `my.env` 内容
- 不在回答中复述任何密钥、token、账号字段
- 不把敏感字段写进报告、日志或代码注释

### 7.2 不要默认改动密钥文件

除非用户明确要求，否则不要改写：

- `my.env`
- `.env`
- 任意本地凭证文件

### 7.3 如果做安全整改，要先说明影响

例如：

- 把 `my.env` 改成未跟踪配置文件
- 更新 `.gitignore`
- 重构环境变量加载逻辑

这些都可能影响团队成员本地运行方式，不能悄悄改。

## 8. 修改规则

### 8.1 默认以“保持数据契约稳定”为第一原则

如果修改任一阶段的输入输出字段，必须同步检查所有下游阶段。

重点字段包括：

- `item_id`
- `dataset`
- `subject`
- `template_name`
- `messages`
- `metadata`
- `model_id`
- `raw_response`
- `gold_answer`
- `parsed_answer`
- `score`

### 8.2 不轻易重跑大数据产物

以下文件是已有实验产物，不要随意覆盖：

- `data/01_prompts.jsonl`
- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`
- `data/03_scored/scored_results.csv`
- `data/04_analysis/*`
- `data/04_mmlu_subject_analysis/*`
- `plots/*`
- `reports/*`

只有在用户明确要求重跑或重生成时，才可以覆盖。

### 8.3 如果只修代码，不要顺手覆盖结果文件

很多任务只需要修脚本或文档，不需要重跑实验。

默认做法：

- 优先修 `src/`
- 保持 `data/`、`plots/`、`reports/` 不变

### 8.4 Phase 2 改动要最谨慎

因为当前 Phase 2 存在“脚本状态”和“已产出数据状态”不一致的问题，任何对 `src/02_api_runner.py` 的改动都要明确说明：

- 修的是 pilot 逻辑还是 full-run 逻辑
- 是否要与 notebook 保持一致
- 是否会影响已有结果复现

## 9. 推荐的工作优先级

如果用户要求继续推进项目，优先级建议如下：

1. 先修 README，使其与 `develop` 的真实结构、真实模型集合、真实分析脚本一致。
2. 统一 `src/02_api_runner.py` 与现有完整实验产物之间的口径，明确 pilot/full-run 两种模式。
3. 视需要清理环境变量管理方式，避免 `my.env` 带来的协作风险。
4. 在已有 `04_analysis.py` 基础上继续扩展统计分析，而不是重新另起一套 notebook 流程。
5. 写报告或结论时，以 `reports/analysis_summary.md` 和 `reports/focused_research_question_discussion_zh.md` 为当前结果基线。

## 10. 后续 agent 的默认行为

后续 agent 在这个仓库中工作时，默认这样做：

1. 先确认当前分支是否为 `develop`。
2. 先读实际代码与结果文件，再决定是否相信 README。
3. 如果任务涉及统计结论，优先读取 `data/04_analysis/`、`data/04_mmlu_subject_analysis/` 和 `reports/`。
4. 如果任务涉及实验复现，先检查 Phase 2 是否仍有 `tasks[:50]` 之类的试跑逻辑。
5. 如果任务涉及文档更新，必须指出“计划版描述”和“当前真实实现”之间的差异。

## 11. 一句话原则

这个仓库现在的正确理解方式是：

它已经是一个“有完整实验产物的 develop 分支项目”，不是一个只写了计划书的课程项目骨架。
