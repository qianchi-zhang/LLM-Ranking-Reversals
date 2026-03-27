# AGENTS.md

## 1. 文件目的

本文件用于约束后续 agent 在本仓库中的工作方式，目标是：

- 维持项目结构清晰
- 保持数据契约稳定
- 避免文档与真实实现脱节
- 不破坏已有实验产物

如果文档、README、计划书和实际代码不一致，默认以 `develop` 分支中的实际脚本和已生成产物为准。

## 2. 当前项目定位

这个仓库不是“只有课程计划书的空骨架”，而是一个已经跑完主体实验、并产出统计分析和图表的项目仓库。

后续 agent 的默认工作方式应当是：

- 理解并维护现有流水线
- 修正文档与实现之间的差异
- 在不破坏产物口径的前提下做增量改进

## 3. 当前标准化结构

```text
LLM-Ranking-Reversals/
├─ src/                              # 实验脚本
├─ data/                             # 数据与中间产物
├─ plots/                            # 图表
├─ reports/                          # 分析讨论
├─ docs/                             # 架构与复现文档
├─ README.md                         # 项目入口说明
├─ AGENTS.md                         # 协作规则
├─ requirements.txt                  # 依赖
└─ my.env                            # 本地密钥配置
```

### 目录语义

- `src/`：只放可执行实验代码
- `data/`：只放数据和统计结果
- `plots/`：只放最终图表
- `reports/`：只放分析性文字产物
- `docs/`：只放结构、规范、复现说明
- `docs/history/`：放历史计划、技术栈和开发日志
- `docs/archive/`：放 proposal、反馈和历史材料
- `src/legacy/`：放非标准流水线的历史脚本

不要把运行脚本塞进 `reports/`，也不要把结果讨论塞进 `src/`。

## 4. 当前真实流水线

### Phase 1：数据抽样与 Prompt 生成

主文件：

- `src/01_data_prep.py`

输入来源：

- `cais/mmlu`
- `allenai/ai2_arc`
- `Rowan/hellaswag`

输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2：OpenRouter 推理

主文件：

- `src/02_api_runner.py`
- `src/02_api_runner.ipynb`

输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

事实说明：

- 当前仓库中已提交的 Phase 2 结果实际来自 `src/02_api_runner.ipynb` 的全量运行
- 当前 `src/02_api_runner.py` 是按 notebook 口径重写的脚本版
- 后续复现时，优先使用脚本版；若讨论历史结果来源，则明确说明它来自 notebook 运行

### Phase 3：答案解析与打分

主文件：

- `src/03_scorer.py`

输出：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4：Bootstrap 统计分析

主文件：

- `src/04_analysis.py`
- `src/04_mmlu_subject_bootstrap.py`

输出：

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`
- `plots/`
- `reports/`

## 5. 当前实验口径

### 数据规模

- 原始题目：900
- prompt request：3600
- 评分结果：14400

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

注意：

- 历史计划文档里提到过 Claude
- 当前真实实现和真实产物不使用 Claude
- 所有结论、README 和复现说明都应以当前真实模型集合为准

## 6. 修改原则

### 6.1 默认不破坏已有产物

以下内容默认视为“已完成实验产物”，不要随意覆盖：

- `data/01_prompts.jsonl`
- `data/02_raw_responses.*`
- `data/03_scored/*`
- `data/04_analysis/*`
- `data/04_mmlu_subject_analysis/*`
- `plots/*`
- `reports/*`

除非用户明确要求重跑或重生成，否则不要覆盖。

### 6.2 数据契约优先

如果修改阶段输入输出字段，必须同步检查所有下游脚本。

关键字段包括：

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

### 6.3 优先做“标准化补强”，不要做“无必要重构”

优先：

- 修复 README 与实际结构不一致
- 增补复现说明
- 清理历史绝对路径
- 统一脚本与 notebook 口径

谨慎：

- 移动大型数据文件
- 重命名已被多个文档引用的结果目录
- 推倒重写整个流水线

## 7. 文档规则

### 7.1 README 必须与真实实现一致

如果 README 写的结构、模型、脚本入口与实际不一致，README 必须优先被修正。

### 7.2 `docs/` 是标准化说明层

后续新增结构说明、复现说明、规范说明，优先放到 `docs/`。

### 7.3 历史文档视为“参考”，不是“最终真相”

以下文件可保留，但它们不一定反映当前真实实现：

- `docs/history/PROJECT_PLAN.md`
- `docs/history/PROJECT_LOG.md`
- 早期 proposal PDF

如果引用它们，必须说明这是历史计划或历史记录。

## 8. 安全规则

### 8.1 不泄露密钥

仓库当前使用 `my.env` / `.env` 加载 `OPENROUTER_API_KEY`。

后续 agent 必须：

- 不打印密钥内容
- 不在回复里复述 token
- 不把密钥写入新的文档、日志或报告

### 8.2 不擅自改凭证文件

除非用户明确要求，否则不要修改：

- `my.env`
- `.env`
- 其他本地凭证文件

## 9. 推荐工作顺序

如果用户要求继续完善项目，推荐优先级如下：

1. 保证 `README.md` 与真实结构一致
2. 保证 `docs/` 中的架构与复现说明完整
3. 保证 `src/02_api_runner.py` 与已产出结果口径一致
4. 在现有分析脚本基础上扩展统计分析
5. 再考虑更大的结构重构

## 10. 一句话原则

后续 agent 在这个仓库中工作时，应把它当成一个“已有完整实验产物、需要标准化维护与可复现增强”的项目，而不是一个还未开始实现的课程作业模板。
