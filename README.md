# ST5230 Project: LLM Ranking Reversals

**Group 14 Team Members:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## 项目简介

本项目研究 LLM benchmark 的评测稳定性，关注的不是单纯的“谁更强”，而是：

- 非语义 prompt 扰动是否会改变模型表现
- 测试子集变化是否会改变模型相对排名
- 这些波动是否足以引发 ranking reversal，从而削弱静态 leaderboard 的解释力

当前 `develop` 分支已经包含完整的实验流水线、主要实验产物、统计分析表和图表，因此这个仓库应被视为“已完成主体实验的项目仓库”，而不是只有规划文档的骨架仓库。

## 当前实验设置

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

注意：这与早期计划文档中的 Claude 方案不一致。最终报告、复现实验和结论解释应以当前仓库中的真实代码与真实产物为准。

## 标准化项目结构

```text
LLM-Ranking-Reversals/
├─ src/                              # 核心实验脚本
│  ├─ 01_data_prep.py
│  ├─ 02_api_runner.py
│  ├─ 02_api_runner.ipynb
│  ├─ 03_scorer.py
│  ├─ 04_analysis.py
│  └─ 04_mmlu_subject_bootstrap.py
├─ data/                             # 数据与中间产物
│  ├─ 00_raw_question.jsonl
│  ├─ 01_prompts.jsonl
│  ├─ 02_raw_responses.jsonl
│  ├─ 02_raw_responses.csv
│  ├─ 03_scored/
│  ├─ 04_analysis/
│  └─ 04_mmlu_subject_analysis/
├─ plots/                            # 最终图表
├─ reports/                          # 分析讨论与结果摘要
├─ docs/                             # 架构与复现说明
├─ README.md                         # 项目入口说明
├─ AGENTS.md                         # 协作与修改边界
├─ PROJECT_PLAN.md                   # 历史计划文档
├─ PROJECT_LOG.md                    # 历史开发日志
├─ TECH_STACK.md                     # 技术栈说明
└─ requirements.txt                  # Python 依赖
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

输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

当前仓库中已提交的 Phase 2 结果实际来自 `src/02_api_runner.ipynb` 的全量运行。现在的 `src/02_api_runner.py` 是与 notebook 口径对齐的脚本化版本，适合后续复现。

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

## 环境与依赖

推荐使用 Python 3.11。

安装依赖：

```bash
pip install -r requirements.txt
```

如果需要隔离环境，推荐使用 `conda` 或 `venv`。

## API Key 配置

当前 Phase 2 的 notebook 运行口径使用的是仓库根目录下的 `my.env`。为了兼容不同本地环境，脚本版 `src/02_api_runner.py` 会优先读取 `my.env`，其次读取 `.env`。

示例格式：

```text
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
```

不要把真实密钥提交到 GitHub。

## Phase 2 复现方式

为了避免“脚本默认只跑小样本，但仓库里却放着全量结果”的口径混乱，当前脚本使用显式模式控制。

与当前仓库结果对应的真实运行口径是：

- 输入：`data/01_prompts.jsonl`
- Prompt 来源：每条记录的 `messages[0].content`
- 模型：`GPT-4o-mini`、`Gemini-2.0-flash`、`Qwen-2.5-7B`、`Llama-3.1-8B`
- 解码设置：`temperature=0`、`max_tokens=150`
- 运行方式：全量任务，不做隐式截断

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

## 当前仓库中已存在的主要产物

当前 `develop` 分支中已包含完整实验产物，至少包括：

- 900 条原始题目
- 3600 条 prompt request
- 14400 条模型评分结果
- 主体 bootstrap 分析表
- MMLU subject 级 bootstrap 分析表
- 图表与分析报告草稿

因此，日常开发默认应以“维护和扩展现有流水线”为主，而不是重新从零搭项目结构。

## 关键结果摘要

基于当前仓库中的分析产物：

- `ARC-Challenge` 上排名最稳定，RRR 很低
- `HellaSwag` 上排名最不稳定，prompt 改写可明显改变榜单
- `MMLU` 上 Gemini 稳定领先，但中间梯队仍存在不确定性

详细结果见：

- `reports/analysis_summary.md`
- `reports/focused_research_question_discussion.md`
- `reports/focused_research_question_discussion_zh.md`
- `reports/mmlu_subject_bootstrap_summary.md`

## 文档导航

建议按以下顺序阅读：

1. `README.md`：快速了解项目
2. `docs/ARCHITECTURE.md`：理解标准化架构与层次边界
3. `docs/REPRODUCIBILITY.md`：按照规范复现实验
4. `AGENTS.md`：了解协作和修改规则
5. `reports/`：查看结论与讨论

## 说明

如果 `README.md`、`PROJECT_PLAN.md`、早期 proposal 和实际代码不一致，请优先相信：

1. `develop` 分支中的实际脚本
2. `data/` 下的真实产物
3. `reports/` 中的分析说明
4. `docs/` 中的标准化架构说明
