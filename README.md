# ST5230 Project: LLM Ranking Reversals

**Group 14** Team Members: ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## About The Project

This repository contains the codebase for our ST5230 (Applied Natural Language Processing) course project. We study the statistical reliability of LLM benchmarks, focusing on how non-semantic prompt perturbations and sampling noise can induce ranking reversals among state-of-the-art models.

## Project Goals

- Measure ranking stability under prompt variations and resampling noise.
- Quantify ranking reversal rates across common benchmarks.
- Produce reproducible analysis with transparent data and code.

## Method Overview

1. Sample balanced subsets from MMLU, ARC-Challenge, and HellaSwag.
2. Generate four prompt variants per question (minimal, benchmark-style, minor variation, order/phrasing variation).
3. Run multiple LLMs with fixed decoding parameters (temperature 0, top_p 1).
4. Parse answers, score against gold labels, and compute accuracy.
5. Bootstrap resample to estimate confidence intervals and ranking reversal rates.

## Models (Planned)

- `openai/gpt-4o-mini`
- `anthropic/claude-3.5-haiku`
- `google/gemini-2.0-flash-001`
- `meta-llama/llama-3.1-8b-instruct`

## Repository Structure (WIP)

- `data/` - Sampled evaluation subsets and intermediate artifacts.
- `src/` - Prompt generation, API orchestration, and scoring utilities.
- `notebooks/` - Bootstrap resampling and statistical analysis.
- `docs/` - Planning notes and final report materials.

## Status

Planning complete. Implementation and experiments are in progress.

## Getting Started (Planned)

1. Create a Python 3.10+ environment.
2. Install dependencies from `requirements.txt`.
3. Run data prep to build `master_prompts.jsonl`.
4. Execute API runner to collect `raw_responses.jsonl`.
5. Score results to generate `scored_results.csv`.
6. Analyze with the notebook to produce plots and reversal metrics.

## Outputs (Planned)

- `master_prompts.jsonl` - Prompted questions with metadata.
- `raw_responses.jsonl` - Model outputs with timestamps.
- `scored_results.csv` - Binary correctness per model and prompt.
- `plots/` - Figures for the final report.

## References

See `PROJECT_PLAN.md` for the detailed execution plan and experimental protocol.
