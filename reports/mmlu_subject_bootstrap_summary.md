# MMLU Subject Bootstrap Summary

## Current Bootstrap Design

- The original `04_analysis.py` uses plain item-level bootstrap within each dataset.
- For MMLU, that means sampling with replacement from all 300 items pooled together.
- It does not preserve the 6-subject composition during each bootstrap iteration.

## New Subject-Aware Designs

- `overall_pooled`: resample from all 300 MMLU items directly.
- `overall_stratified`: resample within each of the 6 subjects, keeping 50 items per subject in every iteration.
- `subject_only`: run bootstrap separately on each subject's 50 items.

## Comparison of Pooled vs Stratified Full-MMLU Bootstrap

- overall_pooled: Gemini-2.0-flash=85.08%(rank 1), GPT-4o-mini=73.42%(rank 2), Qwen-2.5-7B=70.33%(rank 3), Llama-3.1-8B=60.08%(rank 4)
- overall_stratified: Gemini-2.0-flash=85.08%(rank 1), GPT-4o-mini=73.42%(rank 2), Qwen-2.5-7B=70.33%(rank 3), Llama-3.1-8B=60.08%(rank 4)

## Subject-Level Highlights

- college_medicine: winner is Gemini-2.0-flash at 82.00%; ranking order = Gemini-2.0-flash > GPT-4o-mini > Qwen-2.5-7B > Llama-3.1-8B
- formal_logic: winner is Gemini-2.0-flash at 77.50%; ranking order = Gemini-2.0-flash > Qwen-2.5-7B > GPT-4o-mini > Llama-3.1-8B
- high_school_macroeconomics: winner is Gemini-2.0-flash at 94.50%; ranking order = Gemini-2.0-flash > GPT-4o-mini > Qwen-2.5-7B > Llama-3.1-8B
- high_school_physics: winner is Gemini-2.0-flash at 78.00%; ranking order = Gemini-2.0-flash > GPT-4o-mini > Qwen-2.5-7B > Llama-3.1-8B
- international_law: winner is Gemini-2.0-flash at 88.50%; ranking order = Gemini-2.0-flash > GPT-4o-mini > Qwen-2.5-7B > Llama-3.1-8B
- philosophy: winner is Gemini-2.0-flash at 90.00%; ranking order = Gemini-2.0-flash > Qwen-2.5-7B > GPT-4o-mini > Llama-3.1-8B

## Most Unstable Subjects

- philosophy: mean RRR across non-minimal prompts = 67.93%
- high_school_physics: mean RRR across non-minimal prompts = 62.25%
- college_medicine: mean RRR across non-minimal prompts = 51.55%
- international_law: mean RRR across non-minimal prompts = 45.48%
- formal_logic: mean RRR across non-minimal prompts = 37.82%
- high_school_macroeconomics: mean RRR across non-minimal prompts = 14.50%

## Output Files

- `data/04_mmlu_subject_analysis/mmlu_scheme_overall_accuracy.csv`
- `data/04_mmlu_subject_analysis/mmlu_scheme_rrr.csv`
- `data/04_mmlu_subject_analysis/mmlu_subject_overall_accuracy.csv`
- `data/04_mmlu_subject_analysis/mmlu_subject_prompt_accuracy.csv`
- `data/04_mmlu_subject_analysis/mmlu_subject_rrr.csv`
- `data/04_mmlu_subject_analysis/mmlu_subject_pairwise_significance.csv`
- `plots/mmlu_subject_accuracy.png`
- `plots/mmlu_subject_rrr.png`
