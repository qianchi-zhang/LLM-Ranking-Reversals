# LLM Ranking Reversals

[English](README.md) | [中文](README.zh-CN.md)

**Group 14:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## Project Overview

This repository studies whether LLM benchmark leaderboards remain stable when the evaluation protocol changes in mild but meaningful ways. The project isolates two sources of instability:

- non-semantic prompt variation
- evaluation-subset variation
- resulting ranking reversals between models

The main empirical conclusion is benchmark-dependent. ARC-Challenge is relatively stable, MMLU is moderately stable at the aggregate level but less stable in narrower slices, and HellaSwag is substantially more fragile. The repository therefore treats ranking robustness, not only average accuracy, as a first-class evaluation target.

## Repository Positioning

This is a completed experimental repository, not a starter skeleton. It already contains:

- standardized pipeline code
- generated experiment artifacts
- analysis tables and plots
- report and presentation sources
- archived planning and course materials

The current default branch is `main`.

## Canonical Entry Points

| Purpose | Canonical path |
| --- | --- |
| End-to-end pipeline | `run_pipeline.py` |
| Phase 2 scripted inference | `src/02_api_runner.py` |
| Final slide source | `reports/overleaf_package/presentation.tex` |
| Final report source | `reports/final_report/final_report.tex` |

Optional but non-default materials:

- `src/02_api_runner.ipynb`: interactive notebook companion, not the default reproducibility path
- `docs/history/`: planning and process history
- `docs/archive/`: archived course files and feedback

## Repository Map

```text
LLM-Ranking-Reversals/
|-- run_pipeline.py
|-- src/
|   |-- 01_data_prep.py
|   |-- 01_data_prep_MMLU_subject.py
|   |-- 02_api_runner.py
|   |-- 02_api_runner.ipynb
|   |-- 03_scorer.py
|   |-- 04_analysis.py
|   |-- 04_mmlu_subject_bootstrap.py
|   `-- legacy/
|-- data/
|   |-- 00_raw_question*.jsonl
|   |-- 01_prompts*.jsonl
|   |-- 02_raw_responses*.jsonl / *.csv
|   |-- 03_scored/
|   |-- 04_analysis/
|   |-- 04_mmlu_subject_analysis/
|   `-- 04_mmlu_subject_analysis_expanded/
|-- plots/
|-- reports/
|   |-- final_report/
|   |-- overleaf_package/
|   |-- web_presentation/
|   `-- README.md
|-- docs/
|   |-- ARCHITECTURE.md
|   |-- REPRODUCIBILITY.md
|   |-- history/
|   `-- archive/
|-- AGENTS.md
|-- requirements.txt
`-- my.env
```

## Fastest Reproduction Path

Recommended Python version: `3.11`

```bash
pip install -r requirements.txt
```

Store a real `OPENROUTER_API_KEY` in one of the following:

1. `my.env.local` (preferred for private local use)
2. `.env`
3. `my.env` after local editing

Then run:

```bash
python run_pipeline.py --mode full --overwrite
```

Useful variants:

```bash
python run_pipeline.py --mode pilot --limit 50 --overwrite
python run_pipeline.py --start-phase 2 --mode full --resume
python run_pipeline.py --start-phase 3 --end-phase 4
python run_pipeline.py --start-phase 4 --end-phase 4 --skip-mmlu-subject-bootstrap
```

## Pipeline Structure

### Phase 1: Data Preparation

```bash
python src/01_data_prep.py
```

Main outputs:

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2: Model Inference

```bash
python src/02_api_runner.py --mode full --overwrite
```

Main outputs:

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

`src/02_api_runner.py` is the standard scripted path. `src/02_api_runner.ipynb` is kept only as an interactive companion for inspection and exploratory runs.

### Phase 3: Parsing and Scoring

```bash
python src/03_scorer.py
```

Main outputs:

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4: Resampling Analysis

```bash
python src/04_analysis.py
python src/04_mmlu_subject_bootstrap.py
```

Main outputs:

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis_expanded/`
- `plots/`
- `reports/`

Phase 4 is fully local. It reuses scored outputs and computes accuracy, PRRR, SRRR, confidence intervals, and rank-probability summaries without calling the API again.

## Main Experiment Scope

- Main standardized benchmark pool: 900 questions
- Prompt requests in the main experiment: 3600
- Model responses in the main experiment: 14400
- Auxiliary expanded MMLU extension: 5 subjects x 200 questions, 16000 additional responses

Prompt templates:

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

Models:

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

Decoding settings:

- `temperature=0`
- `max_tokens=150`

## Results and Report Entry Points

Start here if you want the final materials:

- `reports/final_report/final_report.tex`: canonical final report source
- `reports/overleaf_package/presentation.tex`: canonical Beamer presentation source
- `reports/overleaf_package/presentation.pdf`: compiled presentation artifact
- `reports/web_presentation/index.html`: HTML presentation
- `reports/README.md`: report and presentation index

Useful analytical outputs:

- `reports/analysis_summary.md`
- `reports/focused_research_question_discussion.md`
- `reports/conference_style_report_en.md`
- `plots/`
- `data/04_analysis/`
- `data/04_mmlu_subject_analysis_expanded/`

## Documentation Reading Order

1. `README.md`
2. `README.zh-CN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/REPRODUCIBILITY.md`
5. `AGENTS.md`
6. `reports/README.md`

## Historical Materials and Archives

- `docs/history/` stores planning, logging, and process documents.
- `docs/archive/` stores archived course files such as proposal PDFs and feedback.
- `reports/final_report/archive/` stores non-canonical report variants kept for reference.

If historical documents disagree with the current pipeline, prefer the canonical code paths in `run_pipeline.py`, `src/`, the generated outputs under `data/` and `plots/`, and the standardized documents in `docs/`.

## Credentials and Security

- The tracked `my.env` file is a placeholder template, not a real credential file.
- Never commit a real `OPENROUTER_API_KEY`.
- Prefer `my.env.local`, `.env`, or `--env-file` for private local credentials.
