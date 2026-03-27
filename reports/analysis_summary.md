﻿# 实验结果分析与讨论

## 1. 分析目标与口径

本实验的核心问题不是单纯比较“谁的准确率最高”，而是检验两个更重要的问题：

1. prompt 的非语义变化是否会显著改变模型表现；
2. 当测试子集发生变化时，模型排名是否仍然稳定。

为此，我们基于 `data/02_raw_responses.csv` 生成了 `data/03_scored/scored_results.csv`，并对每个数据集分别进行 2000 次 bootstrap 重采样。分析中同时关注三类指标：

- 平均正确率及 95% bootstrap confidence interval；
- 排名逆转率 RRR；
- 模型间差值的 bootstrap 显著性。

需要特别说明的是，当前实际运行的 4 个模型是 `GPT-4o-mini`、`Gemini-2.0-flash`、`Qwen-2.5-7B` 和 `Llama-3.1-8B`。这与 [PROJECT_PLAN.md](../docs/history/PROJECT_PLAN.md) 中原先写的 Claude 不一致，因此后续报告应以实际数据中的模型为准。

## 2. 总体结论

整体上看，prompt 和子集选择确实会影响模型表现与排名，但这种影响并不均匀，而是高度依赖数据集本身的任务性质。

- 在 ARC-Challenge 上，模型排序几乎不受 prompt 或子集扰动影响，Gemini 的领先地位非常稳固。
- 在 MMLU 上，Gemini 同样稳定领先，但中间梯队之间仍然存在一定的不确定性。
- 在 HellaSwag 上，prompt 改写和子集抽样都会明显改变模型相对位置，尤其是第一名与第二名之间的差距并不稳固。

这说明“模型排行榜”不能被理解为某种固定真值。对于更结构化、更接近标准考试题的任务，榜单相对稳定；但对于更依赖语境续写、常识衔接或表述风格的数据集，榜单更容易随着 prompt 和样本选择发生波动。

## 3. 三个数据集的主要结果

### 3.1 ARC-Challenge：高准确率且高稳定性

ARC-Challenge 上的总体平均正确率与排名为：

- Gemini-2.0-flash: 94.00%, 95% CI [91.42%, 96.50%]
- GPT-4o-mini: 90.83%, 95% CI [87.58%, 93.75%]
- Qwen-2.5-7B: 85.08%, 95% CI [81.17%, 88.92%]
- Llama-3.1-8B: 77.33%, 95% CI [73.25%, 82.00%]

这个数据集上有两个非常明显的现象。

第一，榜首几乎不动。Gemini 在不同 prompt 下的 top-1 概率始终非常高：Minimal 为 99.35%，Benchmark 为 95.40%，Natural 为 99.65%，Order/Phrasing 为 99.70%。这意味着无论 prompt 还是 bootstrap 子集怎样变化，ARC 上的第一名几乎总是 Gemini。

第二，RRR 极低。相对于 minimal prompt，其他三种 prompt 的排名逆转率分别仅为：

- Benchmark: 4.70%
- Natural: 1.65%
- Order/Phrasing: 1.05%

这说明 ARC-Challenge 上模型差距是“宽间隔”的。由于 Gemini、GPT、Qwen、Llama 之间性能差异较大，prompt 扰动和抽样噪声不足以频繁改变排序。换句话说，ARC 上的排行榜更接近模型真实能力排序，而不是 prompt 偶然性的产物。

### 3.2 HellaSwag：排名最容易翻转

HellaSwag 上的总体平均正确率与排名为：

- GPT-4o-mini: 89.17%, 95% CI [86.00%, 92.09%]
- Gemini-2.0-flash: 87.25%, 95% CI [84.08%, 90.25%]
- Qwen-2.5-7B: 84.25%, 95% CI [80.83%, 87.75%]
- Llama-3.1-8B: 68.33%, 95% CI [63.92%, 72.75%]

表面上看，GPT-4o-mini 排第一，但这个“第一名”并不牢靠。GPT 与 Gemini 的点估计差值只有 1.92%，其 95% CI 为 [-0.67%, 4.75%]，`p=0.169`，并不显著。这意味着如果只看平均值，GPT 略高于 Gemini；但从统计意义上讲，我们不能有足够把握说 GPT 一定优于 Gemini。

这与 HellaSwag 的高 RRR 完全一致。与 minimal prompt 相比，其余 prompt 的排名逆转率分别达到：

- Benchmark: 62.55%
- Natural: 41.35%
- Order/Phrasing: 38.50%

这组结果是全文最关键的证据之一。它说明在 HellaSwag 这类任务中，prompt 改写已经不是“无关紧要的包装”，而会实质性改变模型相对排名。特别是 Benchmark prompt 下，排行榜与 minimal baseline 不一致的概率已经超过六成。

进一步看 top-1 概率，GPT-4o-mini 虽然仍是最常见的第一名，但它的优势并不压倒性：

- Minimal: GPT top-1 74.60%，Gemini 24.75%
- Benchmark: GPT top-1 90.65%，Gemini 2.35%，Qwen 7.00%
- Natural: GPT top-1 77.85%，Gemini 21.00%
- Order/Phrasing: GPT top-1 67.65%，Gemini 32.30%

这说明 HellaSwag 上榜首位置本身就是“脆弱”的。尤其在 Order/Phrasing prompt 下，Gemini 成为第一名的概率已达到 32.30%，远高于 ARC 或 MMLU 中第二名的反超概率。

从 prompt 敏感性看，HellaSwag 也是波动最大的。Llama 在不同 prompt 下正确率从 59.67% 到 73.67%，波动达到 14 个百分点；Qwen 的波动也达到 6 个百分点。这提示我们：对于偏叙事式、续写式的 benchmark，prompt 表述方式很可能改变模型对任务的理解路径，进而放大模型间的相对差异。

### 3.3 MMLU：榜首稳定，但中游边界不清

MMLU 上的总体平均正确率与排名为：

- Gemini-2.0-flash: 85.08%, 95% CI [81.17%, 88.58%]
- GPT-4o-mini: 73.42%, 95% CI [68.67%, 78.17%]
- Qwen-2.5-7B: 70.33%, 95% CI [65.58%, 75.17%]
- Llama-3.1-8B: 60.08%, 95% CI [55.08%, 65.25%]

MMLU 的特点介于 ARC 和 HellaSwag 之间。

一方面，榜首非常稳定。Gemini 在 4 种 prompt 下 top-1 概率都是 100%，且相对 GPT 的差值为 11.67%，95% CI [6.99%, 16.08%]，显著成立。这说明在 MMLU 这种知识性更强的多学科题目上，Gemini 的领先是稳固的，不依赖某一种特定 prompt。

另一方面，中间梯队的边界没有那么清楚。GPT-4o-mini 与 Qwen 的差值只有 3.08%，95% CI 为 [-1.50%, 7.58%]，`p=0.184`，不显著。这意味着虽然点估计上 GPT 位列第二，但这一位置并不能被视为绝对稳定。

从 RRR 看，MMLU 的排名逆转率分别为：

- Benchmark: 19.60%
- Order/Phrasing: 13.50%
- Natural: 8.05%

相比 ARC，MMLU 的排序更容易变化；但相比 HellaSwag，它仍明显更稳。这说明 MMLU 上的子集波动和 prompt 效应主要影响的是“中间名次”，而不是榜首归属。

## 4. prompt 影响的整体洞察

从三个数据集一起看，可以得到几个关于 prompt 效应的更一般性结论。

### 4.1 prompt 的影响具有明显的数据集依赖性

prompt 扰动并不会对所有 benchmark 产生同等影响。ARC 上，4 个 prompt 的准确率范围非常小，例如 Gemini 只在 93.67% 到 94.33% 之间波动；而 HellaSwag 上，同一模型的波动可能达到数个百分点甚至十几个百分点。

这说明 prompt 敏感性并不是模型本身的固定属性，而是模型能力、任务类型与题目表达形式三者交互后的结果。

### 4.2 Benchmark-style prompt 并不总是“更公平”

一个有意思的现象是，Benchmark-style prompt 并不是简单地降低噪声。在 ARC 和 MMLU 上，它没有显著改变整体结论；但在 HellaSwag 上，Benchmark prompt 反而带来了最高的 RRR，达到 62.55%。

这提示我们：所谓“标准 benchmark prompt”未必具有普适中立性。对于某些任务，它可能改变了模型的解题策略，而不仅仅是统一格式。因此，在论文中把某一种 prompt 写成理所当然的唯一评测口径，是需要谨慎的。

### 4.3 排名翻转往往发生在性能接近的模型之间

我们观察到，排名翻转最频繁出现的 setting，往往也是头部模型差距最小的 setting。

- HellaSwag 上 GPT 与 Gemini 差距不显著，对应最高的排名不稳定性；
- ARC 和 MMLU 上榜首差距更大，对应榜首稳定性也更强；
- MMLU 上第二、第三名之间差距不显著，因此虽然第一名稳定，但中游名次仍有波动空间。

因此，排名逆转并不意味着评测完全失效，而是意味着榜单中某些相邻位置的“统计间隔”过窄，不应被过度解读为确定性差异。

## 5. 子集选择的影响

bootstrap 重采样对应的是“如果我们抽到的是另一组题目，结论会不会变化”。从这个角度看，子集选择确实会影响最终榜单，但影响大小取决于数据集本身的难度结构和区分度。

- ARC-Challenge 的 bootstrap 分布较窄，说明即使换一批题，结论也大概率不变。
- HellaSwag 的 bootstrap 分布更宽，top-1 概率更分散，说明样本组成变化足以改变头部模型排序。
- MMLU 的 bootstrap 噪声不足以推翻 Gemini 的领先，但足以让 GPT 与 Qwen 的相对次序变得不那么确定。

这对我们的实验目的非常重要。它说明排行榜不仅受 prompt 影响，也受“测试集刚好抽到了哪些题”影响。换句话说，模型排名本质上是对“模型 x prompt x 样本子集”三者组合的函数，而不是模型的单一固定属性。

## 6. 方法与结果的启示

基于以上结果，本文可以提出以下几个更有解释力的洞察。

第一，应该区分“绝对表现”与“排序稳定性”。一个模型可以在平均准确率上排名第一，但如果 RRR 高、top-1 概率分散、与第二名差距又不显著，那么它只能被称为“当前设定下的领先者”，而不是“稳健的第一名”。

第二，单一 prompt leaderboard 的外推性有限。尤其在 HellaSwag 这类高敏感 benchmark 上，使用某一个 prompt 得到的排行榜，很可能只是众多合理 prompt 设定中的一个切面。

第三，bootstrap 比单次测试集结果更能反映结论可靠性。仅报告平均准确率容易让人误以为排行榜是稳定的；加入置信区间、rank probability 和 RRR 后，哪些结论稳、哪些结论脆弱就会清晰很多。

## 7. 对论文写作的建议

建议在最终报告中采用以下表述方式：

- 主表使用 prompt-averaged accuracy 作为总体性能指标；
- 每个数据集同时报告 95% CI 和 pairwise significance；
- 将 RRR 和 rank probability heatmap 作为“排名稳定性”证据，而不是只给一个静态 leaderboard；
- 对 HellaSwag 明确写出：头部排名对 prompt 与子集都较敏感，第一名结论不够稳固；
- 对 ARC 和 MMLU 明确写出：Gemini 的领先在当前实验中具有较高稳定性；
- 对 MMLU 的第二名与第三名、以及 HellaSwag 的第一名与第二名，避免使用过强措辞。

## 8. 额外说明

- 解析失败仅有 3 条，占 0.02%，对总体统计影响很小；
- 这 3 条都来自 Llama 的安全拒答，说明安全策略虽然不是本实验的重点，但在某些题目上确实会轻微影响 benchmark 得分；
- 当前图表与结果文件已经生成，可直接用于报告撰写。

## 9. 结果文件

- `data/04_analysis/accuracy_by_dataset_model.csv`
- `data/04_analysis/accuracy_by_dataset_model_prompt.csv`
- `data/04_analysis/pairwise_significance.csv`
- `data/04_analysis/ranking_reversal_rate.csv`
- `data/04_analysis/rank_probability.csv`
- `plots/accuracy_boxplots.png`
- `plots/ranking_reversal_rate.png`
- `plots/arc_challenge_rank_probability_heatmaps.png`
- `plots/hellaswag_rank_probability_heatmaps.png`
- `plots/mmlu_rank_probability_heatmaps.png`
