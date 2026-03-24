# Analysis Summary

## Scope

- Data source: `data/02_raw_responses.csv` scored into `data/03_scored/scored_results.csv`.
- Bootstrap iterations: 2000.
- Baseline prompt for RRR: `minimal_instruction`.

## Key Findings

- Parse failures were rare: 3 / 14400 rows (0.02%).
- ARC-Challenge winner: Gemini-2.0-flash (94.00%, 95% CI [91.42%, 96.50%]); runner-up: GPT-4o-mini (90.83%).
- ARC-Challenge ranking was most unstable under Benchmark (RRR=4.70%) and most stable under Order/Phrasing (RRR=1.05%).
- Strongest supported gap on ARC-Challenge: Gemini-2.0-flash vs Llama-3.1-8B = 16.67% (95% CI [12.50%, 20.67%], p=0.0000).
- HellaSwag winner: GPT-4o-mini (89.17%, 95% CI [86.00%, 92.09%]); runner-up: Gemini-2.0-flash (87.25%).
- HellaSwag ranking was most unstable under Benchmark (RRR=62.55%) and most stable under Order/Phrasing (RRR=38.50%).
- Strongest supported gap on HellaSwag: GPT-4o-mini vs Llama-3.1-8B = 20.83% (95% CI [16.75%, 24.92%], p=0.0000).
- MMLU winner: Gemini-2.0-flash (85.08%, 95% CI [81.17%, 88.58%]); runner-up: GPT-4o-mini (73.42%).
- MMLU ranking was most unstable under Benchmark (RRR=19.60%) and most stable under Natural (RRR=8.05%).
- Strongest supported gap on MMLU: Gemini-2.0-flash vs Llama-3.1-8B = 25.00% (95% CI [19.92%, 30.25%], p=0.0000).

## Recommendations

- Report both absolute accuracy and ranking stability. A model that wins on point estimate but has high RRR should not be described as robust without qualification.
- Use prompt-averaged accuracy for the main leaderboard and keep prompt-specific results in the appendix. This reduces over-reading a single prompt formulation.
- Flag safety-refusal and parse-failure rows explicitly in the paper, because they are rare here but can distort benchmark conclusions when concentrated in one model family.
- When discussing top-vs-second differences, rely on bootstrap confidence intervals instead of raw ranking alone, especially on datasets where the leading pair is close.

## Output Files

- `data/04_analysis/accuracy_by_dataset_model.csv`
- `data/04_analysis/accuracy_by_dataset_model_prompt.csv`
- `data/04_analysis/pairwise_significance.csv`
- `data/04_analysis/ranking_reversal_rate.csv`
- `data/04_analysis/rank_probability.csv`
- `plots/accuracy_boxplots.png`
- `plots/ranking_reversal_rate.png`
- `plots/*_rank_probability_heatmaps.png`
