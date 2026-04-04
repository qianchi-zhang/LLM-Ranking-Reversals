# ST5230 Project: LLM Ranking Reversals

[English](README.md) | [简体中文](README.zh-CN.md)

**Group 14 Team Members:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## 项目简介

本项目研究 LLM benchmark 排名的可靠性。我们关心的不是单纯比较“谁分数最高”，而是检验以下问题：

- 非语义 prompt 扰动是否会改变模型表现；
- 测试子集变化是否会改变模型相对排名；
- 这些波动是否足以引发 ranking reversal，从而削弱静态 leaderboard 的解释力。

当前 `develop` 分支已经包含完整的主实验产物、统计分析结果、图表和报告草稿。这个仓库不是空骨架，而是一个已经完成主体实验、并已标准化以便复现和维护的项目仓库。

## 项目结构

```text
LLM-Ranking-Reversals/
|-- run_pipeline.py
|-- src/
|   |-- 01_data_prep.py
|   |-- 02_api_runner.py
|   |-- 02_api_runner.ipynb
|   |-- 03_scorer.py
|   |-- 04_analysis.py
|   |-- 04_mmlu_subject_bootstrap.py
|   `-- legacy/
|-- data/
|-- plots/
|-- reports/
|-- docs/
|-- AGENTS.md
|-- requirements.txt
`-- my.env
```

说明：

- `run_pipeline.py` 是标准的一键流水线入口。
- `src/02_api_runner.py` 是 Phase 2 的标准脚本入口。
- `src/02_api_runner.ipynb` 作为交互式测试和探索 notebook 保留，不是默认批量复现入口。

## 环境安装

推荐 Python 版本：`3.11`

```bash
pip install -r requirements.txt
```

如果需要隔离环境，推荐使用 `conda` 或 `venv`。

## API 配置

Phase 2 通过 OpenRouter 调用模型。将 `OPENROUTER_API_KEY` 放在仓库根目录的 `my.env` 或 `.env` 中：

```text
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
```

不要把真实密钥提交到 Git。

## 快速复现

默认推荐入口是 `run_pipeline.py`。

### Pilot Run

```bash
python run_pipeline.py --mode pilot --limit 50 --overwrite
```

### Full Run

```bash
python run_pipeline.py --mode full --overwrite
```

### 从 Phase 2 继续

```bash
python run_pipeline.py --start-phase 2 --mode full --resume
```

### 只重跑分析阶段

```bash
python run_pipeline.py --start-phase 3 --end-phase 4
```

### 跳过 MMLU Subject 分析

```bash
python run_pipeline.py --start-phase 4 --end-phase 4 --skip-mmlu-subject-bootstrap
```

## 分阶段入口

### Phase 1：数据准备

```bash
python src/01_data_prep.py
```

输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2：模型推理

```bash
python src/02_api_runner.py --mode full --overwrite
```

输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

`src/02_api_runner.py` 是标准脚本复现入口；`src/02_api_runner.ipynb` 是用于交互式测试、检查和探索运行的辅助 notebook。

### Phase 3：解析与评分

```bash
python src/03_scorer.py
```

输出：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4：重抽样分析

```bash
python src/04_analysis.py
python src/04_mmlu_subject_bootstrap.py
```

输出：

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`
- `plots/`
- `reports/`

Phase 4 不会重新调用 API，而是直接复用
`data/03_scored/scored_results.csv` 中已经固定下来的作答评分，在本地对题目子集做重抽样并计算 accuracy、PRRR 和 SRRR。

## 当前实验口径

### 数据规模

- 900 道原始题目
- 3600 条 prompt request
- 14400 条模型结果

### Prompt 模板

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

### 模型集合

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

### 推理参数

- `temperature=0`
- `max_tokens=150`

## 主要输出

- `reports/analysis_summary.md`
- `reports/focused_research_question_discussion.md`
- `reports/focused_research_question_discussion_zh.md`
- `reports/mmlu_subject_bootstrap_summary.md`
- `reports/conference_style_report_en.md`
- `reports/conference_style_report_zh.md`

## 文档导航

建议按这个顺序阅读：

1. `README.md`
2. `README.zh-CN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/REPRODUCIBILITY.md`
5. `AGENTS.md`
6. `reports/`

## 说明

- `docs/history/` 中的文件属于归档的计划与过程记录，不是默认事实来源。
- 如果历史文档和当前实现不一致，以 `src/`、`data/`、`reports/` 和 `docs/` 中当前标准化说明为准。
