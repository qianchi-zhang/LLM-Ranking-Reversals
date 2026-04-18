# Expanded MMLU Subject Resampling Summary

## Scope

- Data source: `data/02_raw_responses_MMLU_subjects.csv` scored into `data/03_scored/mmlu_subjects_scored_results.csv`.
- Subjects analyzed: `high_school_mathematics`, `conceptual_physics`, `high_school_world_history`, `philosophy`, `sociology`.
- Items per subject: 200.
- Resampling iterations per subject: 1000.
- Each subject subset uses 100 items drawn without replacement from that subject's 200-item pool.

## Data Check

- Total scored rows: 16000.
- Parse failures: 0 rows.

## Key Findings

- MMLU_S1 (high_school_mathematics): winner is Gemini-2.0-flash at 62.75%; max PRRR = T1 Minimal vs T3 Natural (32.20%); max SRRR = T1 Minimal (38.70%).
- MMLU_S2 (conceptual_physics): winner is Gemini-2.0-flash at 90.50%; max PRRR = T1 Minimal vs T3 Natural (25.60%); max SRRR = T3 Natural (26.20%).
- MMLU_S3 (high_school_world_history): winner is Gemini-2.0-flash at 91.38%; max PRRR = T1 Minimal vs T3 Natural (74.30%); max SRRR = T1 Minimal (55.00%).
- MMLU_S4 (philosophy): winner is Gemini-2.0-flash at 87.38%; max PRRR = T1 Minimal vs T3 Natural (56.10%); max SRRR = T1 Minimal (49.00%).
- MMLU_S5 (sociology): winner is GPT-4o-mini at 89.38%; max PRRR = T1 Minimal vs T3 Natural (54.30%); max SRRR = T1 Minimal (67.90%).

## Output Files

- `data/03_scored/mmlu_subjects_scored_results.csv`
- `data/03_scored/mmlu_subjects_parse_failures.csv`
- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_overall_accuracy.csv`
- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_prompt_accuracy.csv`
- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_prompt_ranking_reversal_rate.csv`
- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_subset_ranking_reversal_rate.csv`
- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_rank_probability.csv`
- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_subset_accuracy_long.csv`
- `plots/mmlu_subject_expanded_accuracy_boxplots.png`
- `plots/mmlu_subject_expanded_prrr.png`
- `plots/mmlu_subject_expanded_srrr.png`
- `plots/mmlu_subject_expanded_*_rank_probability_heatmaps.png`
