# AGENTS.md

## 1. 文件目的

本文件用于约束后续 agent 在本仓库中的维护方式。目标是：

- 保持仓库结构清晰
- 保持代码、数据和文档口径一致
- 保持最终成果在 GitHub 上可理解、可导航、可复现
- 不破坏已经存在的实验产物

## 2. 仓库定位

本仓库是一个已经完成主实验并保留完整成果的研究型实验仓库，不是待实现的 skeleton。默认维护方向应当是：

- 标准化已有入口
- 修正文档和实现之间的偏差
- 在不破坏现有结果的前提下做增量增强

当前默认主分支是 `main`。

## 3. Canonical Source of Truth

如果不同文件之间出现冲突，默认按以下优先级判断事实来源：

1. `run_pipeline.py` 和 `src/` 中当前可执行脚本
2. `data/`、`plots/`、`reports/` 中当前已保留的实验产物
3. `docs/ARCHITECTURE.md` 与 `docs/REPRODUCIBILITY.md`
4. `README.md` 与 `README.zh-CN.md`
5. `docs/history/` 和 `docs/archive/` 中的历史材料

历史文档只用于追溯背景，不应覆盖当前实现事实。

## 4. 目录语义

- `run_pipeline.py`：端到端统一入口
- `src/`：标准实验脚本
- `src/legacy/`：历史代码归档，不属于默认复现路径
- `data/`：题目、prompt、原始响应、评分结果和分析表格
- `plots/`：最终图表
- `reports/`：报告、slides、HTML presentation 和分析性文字产物
- `docs/`：架构、复现和项目标准化说明
- `docs/history/`：计划、日志、过程记录
- `docs/archive/`：proposal、反馈等课程归档材料

## 5. 标准入口

默认入口固定如下：

- 统一入口：`python run_pipeline.py`
- Phase 1：`python src/01_data_prep.py`
- Phase 2：`python src/02_api_runner.py`
- Phase 3：`python src/03_scorer.py`
- Phase 4：`python src/04_analysis.py`
- 扩展 MMLU 学科分析：`python src/04_mmlu_subject_bootstrap.py`

说明：

- `src/02_api_runner.ipynb` 仅作为交互式补充材料保留
- 最终 slides 权威源文件是 `reports/overleaf_package/presentation.tex`
- 最终报告权威源文件是 `reports/final_report/final_report.tex`

## 6. 数据与输出契约

后续修改若涉及上下游字段，必须检查整条流水线。关键字段包括：

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

标准化默认输出路径包括：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`
- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`
- `data/03_scored/`
- `data/04_analysis/`
- `data/04_mmlu_subject_analysis_expanded/`

## 7. 修改原则

### 7.1 不随意覆盖既有成果

以下内容默认视为实验产物：

- `data/02_raw_responses*`
- `data/03_scored/*`
- `data/04_analysis/*`
- `data/04_mmlu_subject_analysis*/*`
- `plots/*`
- `reports/*`

除非用户明确要求重跑或重生成，否则不要随意覆盖。

### 7.2 文档必须与代码同步

如果修改了以下任一内容，必须同步检查 `README`、`docs/` 和 `AGENTS.md`：

- 入口脚本
- 默认输出路径
- 模型集合
- prompt 模板
- 最终报告或 presentation 的 canonical 路径

### 7.3 优先做标准化，而不是无意义重构

优先事项：

- 修复文档与实现不一致
- 修复编码、路径、分支名等展示问题
- 保持仓库首页和目录说明清晰

避免事项：

- 无必要的大规模目录重构
- 在未确认影响范围前修改 schema
- 把历史材料误当成当前权威实现

## 8. 凭证安全规则

- 不打印、不回传真实 `OPENROUTER_API_KEY`
- 被跟踪的 `my.env` 必须始终是占位符模板
- 本地私有凭证应放在 `my.env.local`、`.env` 或通过 `--env-file` 指定
- 不把真实凭证写入文档、日志、报告或 notebook 输出

## 9. GitHub 展示规则

在不删除关键成果的前提下，保持 GitHub 展示面整洁：

- 保留代码、数据、图表、报告源码、展示源码和历史归档
- 删除明显的编译中间文件和低价值噪音文件
- 保证根目录只放高价值入口文件
- 对保留的历史材料和分发包，用 README 明确说明用途

## 10. 一句话原则

把这个仓库当作“已经有真实实验成果、需要持续标准化并提升公开可读性”的最终展示型研究仓库来维护。
