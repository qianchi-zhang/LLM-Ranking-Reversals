﻿# 围绕原始研究问题的聚焦讨论（中文版）

## 1. 研究问题与项目定位

本项目属于课程主题 **Reliability of LLM Evaluation**。我们真正要回答的问题，不是简单比较“哪个模型最好”，而是检验以下更根本的评测可靠性问题：

1. 在语义不变、仅有表面形式变化的 prompt 条件下，模型准确率是否会发生可观变化；
2. 当测试子集发生变化时，模型之间的性能差距与相对排名是否仍然稳定；
3. 这些波动是否已经大到足以引发 ranking reversal，从而削弱静态 leaderboard 的解释力。

与已有 prompt sensitivity 工作相比，我们的增量不只是说明“分数会波动”，而是进一步考察：**这些波动是否足以改变模型之间的相对排序**。因此，我们关注的不只是 absolute performance sensitivity，更是 **structural ranking stability**。

## 2. 实验流程与数据构建

### 2.1 数据集与题目抽取

我们最终使用了三个自动可评分的四选一多项选择 benchmark，并总共构造了 900 道题目作为 master sample。

- **MMLU**：共抽取 300 题。
  这里不是简单从整体题库中随机取 300 题，而是从 6 个 subject 中各抽取 50 题，总计 300 题。6 个 subject 分别为：
  - `formal_logic`
  - `high_school_macroeconomics`
  - `college_medicine`
  - `high_school_physics`
  - `philosophy`
  - `international_law`
- **ARC-Challenge**：从官方 `test` split 抽取 300 题。
- **HellaSwag**：从 `validation` split 抽取 300 题。之所以不使用 test split，是因为公开 test split 不直接提供 gold label，不适合本项目的自动评分流程。

题目抽取逻辑由 [01_data_prep.py](../src/01_data_prep.py) 实现，抽取后的原始题目保存在 [00_raw_question.jsonl](../data/00_raw_question.jsonl)。

### 2.2 Prompt 生成

对每一道题，我们都生成了 4 个 task-preserving prompt template，因此总共得到：

- 900 道题
- × 4 个 prompt template
- = 3600 个 prompt request

4 个 prompt template 分别是：

1. `minimal_instruction`
2. `benchmark_style`
3. `natural_style`
4. `order_phrasing_variation`

这些 prompt 的变化主要体现在：

- 指令是否更正式；
- 题干与答案格式提醒的顺序；
- 措辞风格是否更自然；
- 问题呈现方式是否略有格式变化。

但所有 template 都保持同一任务语义与同一选项集合不变，因此它们属于 **non-semantic prompt perturbations**。生成后的 prompt 保存在 [01_prompts.jsonl](../data/01_prompts.jsonl)。

### 2.3 模型调用

我们对每个 prompt request 调用了 4 个模型，因此总共得到：

- 3600 个 prompt request
- × 4 个模型
- = 14400 条模型响应

需要特别说明的是，**实际跑通并进入分析的数据中的 4 个模型**为：

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

这与最初 proposal 中写到的 `GPT-4.1 mini / Claude 3.5 Haiku / Gemini / Llama` 并不完全一致。因此最终报告的实验设置部分应当以**实际运行的数据**为准，而不是以最初 proposal 的计划模型表述为准。

原始响应保存在 [02_raw_responses.csv](../data/02_raw_responses.csv)。

### 2.4 答案解析与评分

评分流程由 [03_scorer.py](../src/03_scorer.py) 实现。具体做法是：

1. 从 `metadata` 中读取 gold answer；
2. 从模型原始文本输出中用正则表达式提取 A/B/C/D；
3. 将解析出的选项与 gold answer 比较；
4. 正确记为 1，错误或无法解析记为 0。

最终得到 [scored_results.csv](../data/03_scored/scored_results.csv)。

在 14400 条响应中，仅有 3 条无法正常解析，占比 0.02%，且都来自 Llama 的安全拒答，因此对整体统计结论影响很小。

## 3. 我们到底计算了哪些准确率？

### 3.1 Prompt-specific accuracy

对每个 “dataset × model × prompt template” 组合，我们都计算了一个准确率。

总数为：

- 3 个 dataset
- × 4 个模型
- × 4 个 prompt template
- = **48 个 prompt-specific accuracy**

这些结果保存在 [accuracy_by_dataset_model_prompt.csv](../data/04_analysis/accuracy_by_dataset_model_prompt.csv)。

下面按数据集整理这些准确率。

#### ARC-Challenge

- GPT-4o-mini：
  - Benchmark 91.67%
  - Minimal 90.67%
  - Natural 90.33%
  - Order/Phrasing 90.67%
- Gemini-2.0-flash：
  - Benchmark 93.67%
  - Minimal 94.00%
  - Natural 94.00%
  - Order/Phrasing 94.33%
- Qwen-2.5-7B：
  - Benchmark 84.33%
  - Minimal 84.67%
  - Natural 85.67%
  - Order/Phrasing 85.67%
- Llama-3.1-8B：
  - Benchmark 77.67%
  - Minimal 77.00%
  - Natural 78.00%
  - Order/Phrasing 76.67%

#### HellaSwag

- GPT-4o-mini：
  - Benchmark 90.33%
  - Minimal 86.67%
  - Natural 90.00%
  - Order/Phrasing 89.67%
- Gemini-2.0-flash：
  - Benchmark 87.00%
  - Minimal 85.00%
  - Natural 88.33%
  - Order/Phrasing 88.67%
- Qwen-2.5-7B：
  - Benchmark 87.00%
  - Minimal 81.00%
  - Natural 85.33%
  - Order/Phrasing 83.67%
- Llama-3.1-8B：
  - Benchmark 73.33%
  - Minimal 59.67%
  - Natural 73.67%
  - Order/Phrasing 66.67%

#### MMLU

- GPT-4o-mini：
  - Benchmark 72.33%
  - Minimal 74.00%
  - Natural 74.33%
  - Order/Phrasing 73.00%
- Gemini-2.0-flash：
  - Benchmark 85.00%
  - Minimal 84.67%
  - Natural 85.67%
  - Order/Phrasing 85.00%
- Qwen-2.5-7B：
  - Benchmark 70.33%
  - Minimal 70.33%
  - Natural 70.33%
  - Order/Phrasing 70.33%
- Llama-3.1-8B：
  - Benchmark 60.33%
  - Minimal 60.33%
  - Natural 59.33%
  - Order/Phrasing 60.33%

### 3.2 Prompt-averaged accuracy

除了上面的 48 个 prompt-specific accuracy，我们还对每个 “dataset × model” 组合，将 4 个 prompt 下的准确率取平均，得到总体准确率。

总数为：

- 3 个 dataset
- × 4 个模型
- = **12 个 prompt-averaged accuracy**

结果保存在 [accuracy_by_dataset_model.csv](../data/04_analysis/accuracy_by_dataset_model.csv)。

具体为：

- **ARC-Challenge**：Gemini 94.00% > GPT 90.83% > Qwen 85.08% > Llama 77.33%
- **HellaSwag**：GPT 89.17% > Gemini 87.25% > Qwen 84.25% > Llama 68.33%
- **MMLU**：Gemini 85.08% > GPT 73.42% > Qwen 70.33% > Llama 60.08%

## 4. Bootstrap 与显著性分析是怎么做的？

### 4.1 原始 bootstrap 设计

在最初的 [04_analysis.py](../src/04_analysis.py) 中，我们对每个 dataset 单独进行 bootstrap。

对于任意一个 dataset：

- 共有 300 道题；
- 每次 bootstrap iteration 都从这 300 道题中有放回抽取 300 次；
- 然后在这个 bootstrap 子集上重新计算 4 个模型在 4 个 prompt 下的准确率；
- 共重复 2000 次，形成经验分布。

这意味着：

- ARC-Challenge：从 300 道 ARC 题中直接 bootstrap；
- HellaSwag：从 300 道 HellaSwag 题中直接 bootstrap；
- MMLU：原始版本也是从全部 300 道 MMLU 题中直接 bootstrap，**并不保留 6 个 subject 各 50 题的结构**。

### 4.2 95% 置信区间

对于每个准确率或模型差值，我们都用 bootstrap 分布的 2.5% 和 97.5% 分位数构造 95% confidence interval。

### 4.3 Pairwise significance

我们还计算了模型间的成对差值，并基于 bootstrap 差值分布给出：

- point difference；
- 95% CI；
- bootstrap p-value；
- 差值是否在 95% 水平上显著。

这一步的目的，是避免只看 point estimate 排名而忽略“名次之间其实没有显著差异”的情况。

## 5. RRR 的定义与我们计算了哪些 RRR

### 5.1 RRR 的定义

我们定义 Ranking Reversal Rate（RRR）时，使用 `minimal_instruction` 作为 baseline prompt。

对同一个 bootstrap iteration：

1. 先计算 minimal prompt 下 4 个模型的排名向量，记为 `R_base`；
2. 再计算另一个 prompt template 下 4 个模型的排名向量，记为 `R_variant`；
3. 只要 `R_variant != R_base`，即至少有一个模型的位置发生交换，就记为一次 ranking reversal；
4. 在全部 bootstrap 迭代中，发生 reversal 的比例，就是这个 prompt 相对 minimal 的 RRR。

也就是说，RRR 衡量的不是“分数是否变化”，而是“这种变化是否已经足以改变相对排名”。

### 5.2 我们一共计算了哪些 RRR

在原始三数据集分析中，我们对每个 dataset 都计算了 3 个 RRR：

- `benchmark_style` 相对 `minimal_instruction` 的 RRR；
- `natural_style` 相对 `minimal_instruction` 的 RRR；
- `order_phrasing_variation` 相对 `minimal_instruction` 的 RRR。

因此总共有：

- 3 个 dataset
- × 3 个非 baseline prompt
- = **9 个 dataset-level RRR**

具体结果为：

- **ARC-Challenge**：
  - Benchmark：4.70%
  - Natural：1.65%
  - Order/Phrasing：1.05%
- **HellaSwag**：
  - Benchmark：62.55%
  - Natural：41.35%
  - Order/Phrasing：38.50%
- **MMLU**：
  - Benchmark：19.60%
  - Natural：8.05%
  - Order/Phrasing：13.50%

这些结果保存在 [ranking_reversal_rate.csv](../data/04_analysis/ranking_reversal_rate.csv)。

## 6. 三个数据集的主要结论

### 6.1 ARC-Challenge：高准确率且高稳定性

ARC 上的结论最稳定。Gemini 在 4 个 prompt 下始终保持第一，且 top-1 probability 始终在 95% 以上；相应地，RRR 也很低，仅在 1.05% 到 4.70% 之间。

这说明 ARC 上模型之间的性能差距足够大，prompt 扰动和 subset resampling 带来的噪声不足以经常改变排名。换言之，ARC 上的 leaderboard 在当前实验设定下是相对可信的。

### 6.2 HellaSwag：最容易发生 ranking reversal

HellaSwag 是整个项目里最能支撑原始研究问题的 benchmark。虽然 GPT-4o-mini 在点估计上排名第一，但它相对于 Gemini 的优势只有 1.92%，95% CI 跨过 0，且 `p=0.169`，并不显著。

与此同时，HellaSwag 的 RRR 显著高于另外两个数据集，尤其是 Benchmark prompt 达到 62.55%。这说明：在 HellaSwag 上，prompt 与 subset 的联合扰动已经大到足以让 leaderboard 结论明显不稳。

因此，HellaSwag 上最重要的结论不是“GPT 第一”，而是“第一名本身并不稳固”。

### 6.3 MMLU：总体榜首稳定，但中间名次有不确定性

MMLU 上 Gemini 稳定排第一，且它相对于 GPT 的差距显著，因此榜首本身比较稳。但 GPT 与 Qwen 之间差距不显著，这意味着 MMLU 总榜上的第二、第三名并不是完全稳固的。

所以，MMLU 提供的是一种“顶部稳定、中部不稳定”的模式：总体看来排行榜并不混乱，但中游层级并不能被过度解读。

## 7. 新增实验：MMLU 的 subject-aware 子集实验

### 7.1 为什么要补这个实验？

MMLU 的 300 题并不是来自单一同质任务，而是来自 6 个 subject 各 50 题。如果 bootstrap 时直接把 300 题混在一起抽样，那么每次重采样的 subject composition 其实会漂移，这会把“题目难度差异”和“科目组成差异”混在一起。

因此，我们新增了一个更细粒度的 MMLU 子集实验，专门研究：**如果从不同 subject 构造 bootstrap 子集，MMLU 的稳定性结论会不会改变？**

新增脚本是 [04_mmlu_subject_bootstrap.py](../src/04_mmlu_subject_bootstrap.py)。

### 7.2 新实验采用了哪些 bootstrap 方案？

我们对 MMLU 额外实现了三种分析口径：

1. **overall_pooled**
   - 与原始分析一致；
   - 从全部 300 道 MMLU 题中直接 bootstrap；
   - 不保留 subject 结构。

2. **overall_stratified**
   - 在每次 bootstrap 中，对 6 个 subject 分别有放回抽取；
   - 每个 subject 仍保持 50 道题；
   - 因此每次 iteration 都保留完整的 subject composition。

3. **subject_only**
   - 对每个单独的 subject（50 题）分别做 bootstrap；
   - 用来研究科目内部的 ranking stability。

### 7.3 Pooled 与 stratified 的总体对比

一个重要发现是：在 MMLU 总体层面，`overall_pooled` 与 `overall_stratified` 的 point estimate 和总体排序几乎完全一致：

- Gemini：85.08%，rank 1
- GPT：73.42%，rank 2
- Qwen：70.33%，rank 3
- Llama：60.08%，rank 4

这说明：**MMLU 总榜上的主结论并不是 subject composition 偶然失衡造成的**。即使强制每次 bootstrap 都保持 6 个 subject 各 50 题，总体排行榜也没有变化。

### 7.4 Subject-level 分析揭示了更细的异质性

虽然 MMLU 总榜在 pooled 和 stratified 下都稳定，但一旦按单个 subject 分开看，模型排序就出现了明显差异。

各 subject 的 prompt-averaged 准确率与排序为：

- `college_medicine`：Gemini 82.0% > GPT 76.0% > Qwen 71.0% > Llama 62.0%
- `formal_logic`：Gemini 77.5% > Qwen 69.5% > GPT 60.0% > Llama 48.0%
- `high_school_macroeconomics`：Gemini 94.5% > GPT 83.0% > Qwen 68.5% > Llama 58.5%
- `high_school_physics`：Gemini 78.0% > GPT 54.0% > Qwen 53.5% > Llama 42.0%
- `international_law`：Gemini 88.5% > GPT 85.5% > Qwen 74.5% > Llama 72.5%
- `philosophy`：Gemini 90.0% > Qwen 85.0% > GPT 82.0% > Llama 77.5%

这里最值得注意的是：

- 在 `formal_logic` 上，Qwen 超过了 GPT；
- 在 `philosophy` 上，Qwen 也超过了 GPT；
- 这说明 MMLU 总榜中 “GPT 第二、Qwen 第三” 的结构，并不是每个 subject 内都成立。

换句话说，MMLU 总体的稳定性部分来自于 **不同 subject 混合后的平均化效果**。一旦把 subject 拆开，排名结构会暴露出更多局部异质性。

### 7.5 Subject-level RRR：哪些科目最不稳定？

在 `subject_only` 分析中，我们对每个 subject 都计算了 3 个 RRR，因此一共新增了：

- 6 个 subject
- × 3 个非 baseline prompt
- = **18 个 subject-level RRR**

按 subject 的平均 RRR 来看：

- `philosophy`：67.93%
- `high_school_physics`：62.25%
- `college_medicine`：51.55%
- `international_law`：45.48%
- `formal_logic`：37.82%
- `high_school_macroeconomics`：14.50%

这说明即使都属于 MMLU，不同学科对 prompt 扰动的敏感度也差异很大。尤其是 `philosophy` 和 `high_school_physics`，其 ranking stability 远弱于 MMLU 总榜给人的印象。

## 8. 对原始研究问题的综合结论

综合原始三数据集实验与新增的 MMLU subject-aware 实验，我们可以给出更严谨的结论。

第一，prompt 与 subset selection 确实会影响模型表现与排名，但这种影响不是均匀的，而是 benchmark-specific，甚至在同一 benchmark 内还是 subject-specific 的。

第二，HellaSwag 是最典型的“不稳定 benchmark”。在这个数据集上，leaderboard 对 prompt 和 subset 都很敏感，第一名与第二名之间的差距不显著，RRR 又很高，因此最能说明“静态排行榜可能并不可靠”。

第三，ARC-Challenge 是最稳定的 benchmark。它告诉我们，不能把结论说成“所有 leaderboard 都不可靠”；更准确的说法是，leaderboard 的可靠性本身是一个需要实证检验的属性。

第四，MMLU 在总体层面是“榜首稳定、中游较脆弱”的；而在 subject 层面则进一步显示出局部 ranking reversal。这说明总体 leaderboard 可能掩盖科目内部的结构性异质性。

第五，从实践角度看，评测结果最合理的报告方式不应只是一个静态 leaderboard，而应同时报告：

- prompt-specific accuracy；
- prompt-averaged accuracy；
- 95% confidence intervals；
- pairwise significance；
- rank probability；
- ranking reversal rate。

只有这样，才能把“模型真的更强”与“评测设定刚好对它更有利”区分开来。

## 9. 最适合写进最终报告的总结句

如果用一句话概括本项目，可以写成：

> 既有研究已经表明，LLM 的分数会对 prompt wording 敏感；而我们的工作进一步说明，当 prompt variation 与 subset resampling 被联合考虑时，这些分数波动在某些 benchmark 上已经大到足以改变模型的相对排名。实验结果表明，leaderboard 的可靠性并不是默认成立的，而是一个随 benchmark 与题目组成变化而变化的经验属性。
