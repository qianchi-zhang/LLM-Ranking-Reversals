# ST5230 Project: LLM Ranking Reversals

**Group 14 Team Members:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## 项目简介

本项目研究 LLM benchmark 的评测稳定性，核心问题不是“谁的准确率最高”，而是：

- 非语义 prompt 扰动是否会改变模型表现
- 测试子集变化是否会改变模型相对排名
- 这些波动是否已经大到足以引发 ranking reversal

当前仓库以 `develop` 分支为主工作线，已经包含完整的四阶段流水线、实验结果、统计分析表和可视化图。

## 当前实际实验设置

### 数据集

- `MMLU`：从 6 个 subject 中各抽取 50 题，共 300 题
- `ARC-Challenge`：300 题
- `HellaSwag`：300 题

总计 900 道题，每题生成 4 个 prompt 变体，共 3600 个 prompt request。

### Prompt 模板

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

### 实际参与分析的模型

当前代码与产物中实际使用的 4 个模型是：

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

注意：这与早期计划文档中出现过的 `Claude 3.5 Haiku` 不一致。最终报告和复现实验应以仓库中的真实数据与当前脚本配置为准。

## 当前仓库结构

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
│  ├─ 04_analysis/
│  └─ 04_mmlu_subject_analysis/
├─ plots/
├─ reports/
├─ README.md
├─ AGENTS.md
├─ PROJECT_PLAN.md
├─ PROJECT_LOG.md
├─ TECH_STACK.md
└─ requirements.txt
```

## 四阶段流水线

### Phase 1: 数据抽样与 Prompt 生成

脚本：

- `python src/01_data_prep.py`

输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2: OpenRouter 推理

脚本：

- `python src/02_api_runner.py`
- `src/02_api_runner.ipynb`

输入：

- `data/01_prompts.jsonl`

输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

当前 `02_api_runner.py` 已明确区分 `pilot` 和 `full` 两种模式，不再默认把全量实验静默截断成前 50 条。
当前仓库中已提交的 `data/02_raw_responses.*`、`data/03_scored/*` 和后续分析产物，实际是基于 `src/02_api_runner.ipynb` 的全量运行结果得到的；现在的 `src/02_api_runner.py` 已对齐这套 notebook 口径，并补上了更清晰的命令行接口。

### Phase 3: 答案解析与打分

脚本：

- `python src/03_scorer.py`

输出：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4: Bootstrap 统计分析

脚本：

- `python src/04_analysis.py`
- `python src/04_mmlu_subject_bootstrap.py`

输出：

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`
- `plots/`
- `reports/`

## 环境配置

推荐使用 Python 3.11。

安装依赖：

```bash
pip install -r requirements.txt
```

## API Key 配置

Phase 2 的实际 notebook 运行口径使用的是仓库根目录下的 `my.env`。
当前 `src/02_api_runner.py` 会优先读取 `my.env`，其次读取 `.env`，以兼容不同本地环境。

文件内容格式：

```text
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
```

不要把任何真实密钥提交到 GitHub。

## Phase 2 复现说明

为了避免再次出现“代码默认只跑一小段，但仓库里却放着全量结果”的口径问题，当前脚本使用以下规则：

- 默认模式为 `full`
- 如果输出文件已存在，脚本不会直接覆盖
- 继续已有运行请使用 `--resume`
- 重新完整生成请使用 `--overwrite`

与当前仓库结果对应的真实运行口径是：

- 输入：`data/01_prompts.jsonl`
- 模型：`GPT-4o-mini`、`Gemini-2.0-flash`、`Qwen-2.5-7B`、`Llama-3.1-8B`
- Prompt 来源：每条记录的 `messages[0].content`
- 解码设置：`temperature=0`、`max_tokens=150`
- 运行方式：全量任务，不做 `[:50]` 截断

### Pilot Run

```bash
python src/02_api_runner.py --mode pilot --limit 50 --overwrite
```

### Full Run

```bash
python src/02_api_runner.py --mode full --overwrite
```

### Resume Full Run

```bash
python src/02_api_runner.py --mode full --resume
```

## 当前仓库中已存在的主要实验产物

当前 `develop` 分支中已经包含完整实验产物，至少包括：

- 900 条原始题目
- 3600 条 prompt request
- 14400 条模型响应评分结果
- 主体 bootstrap 分析表
- MMLU subject 级 bootstrap 分析表
- 可视化图和分析报告草稿

因此，这个仓库不是一个“只有计划书的课程项目骨架”，而是一个已经跑完主体实验的项目仓库。

## 关键结果摘要

基于当前仓库中的分析产物：

- `ARC-Challenge` 上排名最稳定，RRR 很低
- `HellaSwag` 上排名最不稳定，prompt 改写可明显改变榜单
- `MMLU` 上 Gemini 稳定领先，但中间梯队仍存在不确定性

更详细的结果见：

- `reports/analysis_summary.md`
- `reports/focused_research_question_discussion.md`
- `reports/focused_research_question_discussion_zh.md`
- `reports/mmlu_subject_bootstrap_summary.md`

## 说明

如果 `README.md`、`PROJECT_PLAN.md`、早期 proposal 和实际代码不一致，请优先相信：

1. `develop` 分支中的实际脚本
2. `data/` 下的真实产物
3. `reports/` 中的分析说明

协作约束和 agent 工作边界见 `AGENTS.md`。
