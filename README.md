# ST5230 Project: LLM Ranking Reversals

[English](README.md) | [Chinese](README.zh-CN.md)

**Group 14 Team Members:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## Overview

This project studies the reliability of LLM benchmark rankings. Instead of asking only which model has the highest score, we focus on three questions:

- Do non-semantic prompt perturbations change model performance?
- Does evaluation-subset variation change relative model rankings?
- Are those changes large enough to trigger ranking reversals and weaken the interpretation of a static leaderboard?

The `develop` branch already contains the full experiment artifacts, statistical analysis outputs, figures, and report drafts. This repository is not a project skeleton; it is a completed experimental repository that has been standardized for reproducibility and maintenance.

## Project Layout

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
|   |-- 00_raw_question.jsonl
|   |-- 01_prompts.jsonl
|   |-- 02_raw_responses.jsonl
|   |-- 02_raw_responses.csv
|   |-- 03_scored/
|   |-- 04_analysis/
|   `-- 04_mmlu_subject_analysis/
|-- plots/
|-- reports/
|-- docs/
|   |-- ARCHITECTURE.md
|   |-- REPRODUCIBILITY.md
|   |-- history/
|   `-- archive/
|-- AGENTS.md
|-- requirements.txt
`-- my.env
```

Notes:

- `run_pipeline.py` is the standard end-to-end entrypoint.
- `src/02_api_runner.py` is the standard CLI entrypoint for Phase 2.
- `src/02_api_runner.ipynb` is kept as an optional notebook for interactive testing and exploratory runs.

## Environment Setup

Recommended Python version: `3.11`

```bash
pip install -r requirements.txt
```

If you prefer isolated environments, use `conda` or `venv`.

## API Configuration

Phase 2 uses OpenRouter. Put `OPENROUTER_API_KEY` in `my.env` or `.env` at the repository root:

```text
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
```

Do not commit real credentials.

## Quick Reproduction

The recommended default entrypoint is `run_pipeline.py`.

### Pilot Run

```bash
python run_pipeline.py --mode pilot --limit 50 --overwrite
```

### Full Run

```bash
python run_pipeline.py --mode full --overwrite
```

### Resume from Phase 2

```bash
python run_pipeline.py --start-phase 2 --mode full --resume
```

### Re-run Analysis Only

```bash
python run_pipeline.py --start-phase 3 --end-phase 4
```

### Skip MMLU Subject Analysis

```bash
python run_pipeline.py --start-phase 4 --end-phase 4 --skip-mmlu-subject-bootstrap
```

## Phase-by-Phase Entry Points

### Phase 1: Data Preparation

```bash
python src/01_data_prep.py
```

Outputs:

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2: Model Inference

```bash
python src/02_api_runner.py --mode full --overwrite
```

Outputs:

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

`src/02_api_runner.py` is the standard reproducibility path for scripted runs. `src/02_api_runner.ipynb` is an optional companion notebook for interactive testing, inspection, and exploratory execution.

### Phase 3: Parsing and Scoring

```bash
python src/03_scorer.py
```

Outputs:

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4: Bootstrap Analysis

```bash
python src/04_analysis.py
python src/04_mmlu_subject_bootstrap.py
```

Outputs:

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`
- `plots/`
- `reports/`

## Current Experiment Scope

### Data Scale

- 900 raw questions
- 3600 prompt requests
- 14400 model results

### Prompt Templates

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

### Models

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

### Decoding Settings

- `temperature=0`
- `max_tokens=150`

## Key Outputs

- `reports/analysis_summary.md`
- `reports/focused_research_question_discussion.md`
- `reports/focused_research_question_discussion_zh.md`
- `reports/mmlu_subject_bootstrap_summary.md`
- `reports/conference_style_report_en.md`
- `reports/conference_style_report_zh.md`

## Documentation

Suggested reading order:

1. `README.md`
2. `README.zh-CN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/REPRODUCIBILITY.md`
5. `AGENTS.md`
6. `reports/`

## Notes

- Files under `docs/history/` are archival planning and process records, not the default source of truth.
- If historical documents and current implementation disagree, prefer `src/`, `data/`, `reports/`, and the standardized docs in `docs/`.
