# ST5230 Project: LLM Ranking Reversals

**Group 14 Team Members:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## 项目简介

本项目研究 LLM benchmark 的评测稳定性。我们关心的不是单纯比较“谁分数最高”，而是检验以下问题：

- 非语义 prompt 扰动是否会改变模型表现；
- 测试子集变化是否会改变模型相对排名；
- 这些波动是否足以引发 ranking reversal，从而削弱静态 leaderboard 的解释力。

当前 `develop` 分支已经包含完整的主实验产物、统计分析结果、图表和讨论文档。这个仓库不是空骨架，而是一个已经跑通主流程、后续继续标准化与维护的课程项目仓库。

## 当前标准化结构

```text
LLM-Ranking-Reversals/
├── run_pipeline.py                    # 统一流水线入口
├── src/                               # 实验脚本
│   ├── 01_data_prep.py
│   ├── 02_api_runner.py
│   ├── 02_api_runner.ipynb
│   ├── 03_scorer.py
│   ├── 04_analysis.py
│   ├── 04_mmlu_subject_bootstrap.py
│   └── legacy/
├── data/                              # 数据与中间产物
│   ├── 00_raw_question.jsonl
│   ├── 01_prompts.jsonl
│   ├── 02_raw_responses.jsonl
│   ├── 02_raw_responses.csv
│   ├── 03_scored/
│   ├── 04_analysis/
│   └── 04_mmlu_subject_analysis/
├── plots/                             # 图表输出
├── reports/                           # 分析总结与讨论
├── docs/                              # 架构、复现与历史文档
│   ├── ARCHITECTURE.md
│   ├── REPRODUCIBILITY.md
│   ├── history/
│   └── archive/
├── AGENTS.md                          # 协作规则
├── requirements.txt                   # Python 依赖
└── my.env                             # 本地 API Key 配置
```

## 环境安装

推荐使用 Python 3.11。

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

## 推荐入口：统一运行流水线

项目现在提供统一入口 [run_pipeline.py](/d:/ST5230/LLM-Ranking-Reversals/run_pipeline.py)，默认按 `01 -> 04` 顺序串联运行全部阶段。

### Pilot Run

```bash
python run_pipeline.py --mode pilot --limit 50 --overwrite
```

### Full Run

```bash
python run_pipeline.py --mode full --overwrite
```

### Resume Full Run

```bash
python run_pipeline.py --start-phase 2 --mode full --resume
```

### 只重跑分析阶段

```bash
python run_pipeline.py --start-phase 3 --end-phase 4
```

默认 Phase 4 会依次运行：

- `src/04_analysis.py`
- `src/04_mmlu_subject_bootstrap.py`

如果只想跑主分析而跳过 MMLU subject 分析：

```bash
python run_pipeline.py --start-phase 4 --end-phase 4 --skip-mmlu-subject-bootstrap
```

## 分阶段脚本入口

### Phase 1: 数据抽样与 Prompt 生成

```bash
python src/01_data_prep.py
```

输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2: OpenRouter 推理

```bash
python src/02_api_runner.py --mode full --overwrite
```

输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

当前仓库中已提交的完整 Phase 2 结果历史上来自 `src/02_api_runner.ipynb` 的全量运行；当前的 `src/02_api_runner.py` 已按 notebook 的成功口径对齐，作为标准脚本复现入口。

### Phase 3: 答案解析与评分

```bash
python src/03_scorer.py
```

输出：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4: Bootstrap 分析

```bash
python src/04_analysis.py
python src/04_mmlu_subject_bootstrap.py
```

输出：

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`
- `plots/`
- `reports/`

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

### 实际参与分析的模型

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

### 当前标准推理参数

- `temperature=0`
- `max_tokens=150`

## 主要结果文件

- [analysis_summary.md](/d:/ST5230/LLM-Ranking-Reversals/reports/analysis_summary.md)
- [focused_research_question_discussion.md](/d:/ST5230/LLM-Ranking-Reversals/reports/focused_research_question_discussion.md)
- [focused_research_question_discussion_zh.md](/d:/ST5230/LLM-Ranking-Reversals/reports/focused_research_question_discussion_zh.md)
- [mmlu_subject_bootstrap_summary.md](/d:/ST5230/LLM-Ranking-Reversals/reports/mmlu_subject_bootstrap_summary.md)

## 文档导航

建议按这个顺序阅读：

1. [README.md](/d:/ST5230/LLM-Ranking-Reversals/README.md)
2. [ARCHITECTURE.md](/d:/ST5230/LLM-Ranking-Reversals/docs/ARCHITECTURE.md)
3. [REPRODUCIBILITY.md](/d:/ST5230/LLM-Ranking-Reversals/docs/REPRODUCIBILITY.md)
4. [AGENTS.md](/d:/ST5230/LLM-Ranking-Reversals/AGENTS.md)
5. `reports/`
6. `docs/history/`

## 说明

- `docs/history/` 中的文件属于历史计划与过程记录，不一定完全等于最终实现。
- 如历史文档与当前代码、数据产物不一致，以 `src/`、`data/`、`reports/` 和 `docs/` 中当前标准化说明为准。
