# Focused Discussion on the Original Research Question

## 1. What Question Are We Actually Answering?

According to the proposal and the course theme "Reliability of LLM Evaluation", our project is not mainly about finding the single best model. The original question is whether small and seemingly innocuous evaluation choices, especially prompt wording and subset selection, can materially change reported model performance and even alter model rankings.

Our results give a clear answer: yes, they can, but the size of the effect depends strongly on the benchmark. The instability is not uniform across tasks.

## 2. What Does This Project Add Beyond Existing Prompt-Sensitivity Work?

The feedback notes that the report should explain more clearly what this study adds beyond prior work on benchmark reliability and ranking instability. The main added value of our project is that we do not stop at score variance.

Most prompt-sensitivity analyses ask whether a model's average score moves when the prompt changes. Our project goes one step further and asks whether those score shifts are large enough to change the relative ordering between models. In other words, we shift the focus from absolute performance sensitivity to structural ranking stability.

More specifically, our contribution is the joint analysis of two sources of evaluation noise:

- prompt noise: non-semantic prompt perturbations that alter phrasing, format, or instruction order;
- subset noise: bootstrap resampling over the evaluation items to simulate what would happen if the test set composition changed.

This matters because a leaderboard can look stable in terms of mean scores while still being unstable in terms of rank. Our study therefore provides a more decision-relevant reliability signal: not just "does accuracy move?" but "does the winner change, and under what conditions?"

## 3. Direct Answer to the Original Research Question

Our evidence suggests three main conclusions.

### 3.1 Prompt and subset choices do affect model rankings

The strongest evidence comes from HellaSwag. Relative to the minimal prompt baseline, the ranking reversal rate reaches:

- 62.55% under the Benchmark prompt,
- 41.35% under the Natural prompt,
- 38.50% under the Order/Phrasing prompt.

This means that on HellaSwag, once we change the prompt and resample the subset, the ranking differs from the baseline in a large fraction of bootstrap runs. In practical terms, the leaderboard is not robust.

### 3.2 The effect is benchmark-dependent rather than universal

The same perturbation does not have the same consequence across datasets.

- On ARC-Challenge, RRR stays between 1.05% and 4.70%, indicating that the leaderboard is highly stable.
- On MMLU, RRR is moderate, from 8.05% to 19.60%, indicating some instability but mostly in middle ranks.
- On HellaSwag, RRR is much higher, showing that the benchmark is substantially more sensitive to prompt and subset choices.

So the main finding is not simply that "prompt matters"; it is that benchmark reliability itself varies across tasks. Some leaderboards are robust, while others are highly contingent on evaluation design.

### 3.3 Ranking reversals happen when score gaps are narrow

The most unstable settings are also the settings where model differences are statistically small.

- On HellaSwag, GPT-4o-mini ranks first on point estimate, but its advantage over Gemini-2.0-flash is only 1.92% and not statistically significant (`p=0.169`).
- On MMLU, Gemini is clearly first, but GPT-4o-mini and Qwen-2.5-7B are not significantly separated (`p=0.184`), so second and third place are less stable.
- On ARC-Challenge, Gemini's lead over GPT is significant and the overall ranking is correspondingly stable.

This shows that ranking reversals are not random accidents. They are most likely when models are genuinely close and the evaluation noise is on the same order as the performance gap.

## 4. Especially Informative Ranking-Reversal Cases

The feedback also asks for especially informative cases showing when prompt changes are most likely to alter model comparisons. The most useful cases are not necessarily the ones where the point-estimate order flips outright in the observed sample, but the ones where prompt changes make the bootstrap rank distribution visibly less stable.

### Case 1. HellaSwag, Minimal vs Order/Phrasing: the top rank becomes fragile

This is the cleanest illustration of prompt-induced ranking fragility at the top of the leaderboard.

Under the Minimal prompt, the probability of being rank 1 is:

- GPT-4o-mini: 74.60%
- Gemini-2.0-flash: 24.75%

Under the Order/Phrasing prompt, the rank-1 probabilities become:

- GPT-4o-mini: 67.65%
- Gemini-2.0-flash: 32.30%

The winner does not deterministically flip, but the head-to-head contest becomes much more ambiguous. This is exactly the kind of case where a static leaderboard is misleading: GPT still appears first on average, yet the bootstrap ranking distribution says the top position is contestable.

### Case 2. HellaSwag, Benchmark prompt: prompt changes reshape the whole upper ranking structure

The Benchmark prompt produces the highest RRR in the entire project, 62.55%. It is therefore the most informative "stress test" for ranking stability.

Under this prompt:

- GPT-4o-mini remains the most likely winner, with top-1 probability 90.65%;
- but Gemini and Qwen become much less cleanly separated in the middle of the ranking;
- Gemini is rank 2 in 46.6% of bootstrap runs and rank 3 in 51.0%;
- Qwen is rank 2 in 45.0% of runs and rank 3 in 48.0%.

This is a strong example of how prompt changes need not only affect the winner. They can also destabilize the internal ordering of the top tier. In other words, even when rank 1 looks fairly stable, the broader model hierarchy can still be highly prompt-dependent.

### Case 3. MMLU, Benchmark prompt: prompt changes mostly destabilize the middle ranks, not the winner

MMLU provides a different type of reversal case.

Gemini remains rank 1 with probability 100% across all four prompt templates, so the winner is robust. However, the competition between GPT-4o-mini and Qwen becomes less stable under the Benchmark prompt:

- GPT-4o-mini is rank 2 in 76.0% of bootstrap runs and rank 3 in 24.0%;
- Qwen is rank 2 in 24.0% of runs and rank 3 in 75.8%.

Compared with the Minimal prompt, where GPT is rank 2 in 91.6% of runs, this is a meaningful loss of ranking certainty. This case shows that prompt changes can matter even when the top model is unchanged. The instability can concentrate in the middle of the leaderboard.

### Case 4. ARC-Challenge as a contrast case: when prompt changes are least likely to alter comparisons

ARC is useful as a negative case because it shows the conditions under which prompt changes do not meaningfully alter model comparisons.

- Gemini is rank 1 with 95.4% to 99.7% probability across prompt templates.
- GPT is almost always rank 2.
- Qwen is almost always rank 3.
- Llama is almost always rank 4.

This tells us that ranking reversals are least likely when score gaps are wide and the task is less sensitive to stylistic prompt variation. Including ARC in the discussion is important because it prevents us from overclaiming that all LLM leaderboards are unreliable. The more precise conclusion is that reliability is benchmark-specific.

## 5. Final Conclusions for the Report

If we frame the project around the original research question, the final conclusion should be the following.

First, LLM rankings are not universally reliable point estimates. Their reliability depends on both prompt design and subset composition.

Second, prompt perturbations and subset resampling are not just minor sources of noise. On some benchmarks, especially HellaSwag, they are large enough to make the reported ranking meaningfully unstable.

Third, leaderboard stability should be treated as an empirical property of the benchmark, not an assumption. ARC-Challenge is comparatively robust; MMLU is robust at the top but less so in the middle; HellaSwag is the clearest case where ranking conclusions are fragile.

Fourth, the most useful way to report evaluation results is therefore not only to publish a single leaderboard, but to accompany it with error bars, rank probability summaries, and ranking-reversal statistics. This is the practical implication of our study.

## 6. Suggested Positioning Sentence for the Final Report

A concise way to position the project relative to prior work is:

> Prior work has shown that LLM scores can be sensitive to prompt wording. Our study extends this line of inquiry by asking whether such score fluctuations are large enough to change the relative ranking between models once prompt variation and subset resampling are considered jointly. We find that leaderboard reliability is benchmark-dependent: some rankings remain highly stable, while others, especially on HellaSwag, are fragile under small evaluation changes.
