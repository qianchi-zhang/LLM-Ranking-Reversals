﻿# 如果换一种问法，LLM 排名会改变吗？
## 基于非语义 Prompt 扰动与子集重采样的排名逆转分析

**ST5230 Group 14**  
ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## 摘要

静态 leaderboard 默认假设模型排名在合理的评测设定变化下保持稳定。本文检验这一假设。我们研究非语义 prompt 扰动与评测子集变化是否足以改变三个多项选择 benchmark 上的模型排名：MMLU、ARC-Challenge 与 HellaSwag。我们构建了 900 道题目，将其扩展为 3,600 条 prompt request，并收集 GPT-4o-mini、Gemini-2.0-flash、Qwen-2.5-7B 和 Llama-3.1-8B 的 14,400 条响应。我们对所有输出进行自动评分，并在每个数据集上进行 2,000 次 bootstrap 重采样，以估计置信区间、成对显著性、rank probability 和 ranking reversal rate（RRR）。结果表明，排名稳定性高度依赖 benchmark 本身。ARC-Challenge 极为稳定，MMLU 中等稳定且不确定性主要集中在中间名次，而 HellaSwag 明显更不稳定，在某一 prompt 变体下的排名逆转率达到 62.55%。这些结果说明，leaderboard 的解释应区分平均准确率与排名稳健性，而单一 prompt、单一 split 的评测会高估模型排序的确定性。

## 1. 引言

大语言模型评测通常以 leaderboard 的形式呈现。模型被赋予 benchmark 分数，按准确率排序，再将这个顺序视作模型相对能力的稳定摘要。这种做法方便，但它隐含了一个很强的前提：只要任务本身不变，评测细节上的小变化不应显著改变模型之间的相对排序。

这个前提并不当然成立。即使底层任务保持不变，prompt 措辞、答案格式提醒和指令顺序也可能改变模型的行为；同样，一个 benchmark 分数也依赖于恰好被纳入评测的题目子集。如果模型间的真实差距较小，那么 prompt 噪声或样本组成噪声就可能足以改变“谁排第一”的结论。

因此，本文从**排名稳定性**而非单纯分数波动的角度研究 leaderboard 的可靠性。我们不仅问 prompt 扰动是否会改变准确率，更问一个更严格的问题：**这些变化是否已经大到足以改变模型之间的相对排序？**

本文的贡献主要有三点：

1. 我们不只使用单一 benchmark prompt，而是在四类 task-preserving prompt 下分析排名稳定性。
2. 我们将 prompt 扰动与 bootstrap 子集重采样结合起来，同时量化 prompt 噪声与样本组成噪声。
3. 我们不仅报告平均准确率和置信区间，还显式报告 ranking reversal rate、rank probability 和成对显著性，从而直接刻画排序稳健性。

整体结论是：如果换一种问法，排名确实可能改变，但这种现象并不是在所有 benchmark 上都同样严重。

## 2. 相关工作视角

本文与三类已有研究密切相关。

第一类是 benchmark 构建工作。MMLU、ARC 和 HellaSwag 分别代表多学科知识、多步推理以及常识续写等不同类型的评测场景，为我们的实验提供了任务基础（Hendrycks et al., 2020；Clark et al., 2018；Zellers et al., 2019）。

第二类是 prompt 鲁棒性研究。相关工作表明，大语言模型对 prompt 形式具有显著敏感性，即使任务语义不变，prompt 的不同写法也可能改变输出。PromptRobust 系统性评估了模型对 prompt 扰动的脆弱性（Zhu et al., 2023）。

第三类是评测可靠性讨论。越来越多的工作指出，评测结果并不只是模型本身的属性，也受到协议设计、样本选择和实现细节的影响。本文在这一视角上进一步推进，重点关注这些扰动是否会改变**模型排序结构**。

## 3. 问题定义

设模型为 m，prompt 模板为 p，benchmark 数据集为 D。对每个数据集，我们在多个 prompt 模板和多次 bootstrap 重采样下估计模型表现。

本文关注三个问题：

1. 非语义 prompt 改写是否会改变模型准确率？
2. 在评测子集变化时，这些准确率有多大的不确定性？
3. 这些变化是否足以改变模型之间的排序？

因此，我们真正关心的对象并不是单一的点估计准确率，而是由 prompt 与样本扰动共同诱导出的**排名分布**。

## 4. 实验设计

### 4.1 数据集与抽样

我们使用三个可自动评分的四选一 benchmark：

- **MMLU**：共 300 题，从 6 个 subject 中各抽取 50 题，分别为 `formal_logic`、`high_school_macroeconomics`、`college_medicine`、`high_school_physics`、`philosophy`、`international_law`。
- **ARC-Challenge**：从官方 test split 抽取 300 题。
- **HellaSwag**：从 validation split 抽取 300 题，因为公开 test split 不提供 gold label。

这样得到总计 **900 道题目** 的 master sample。

### 4.2 Prompt 模板

对每道题，我们构造四类 task-preserving prompt：

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

这些模板保持任务语义与答案集合不变，只改变呈现风格、指令口吻和信息顺序。900 道题在 4 个模板下扩展为 **3,600 条 prompt request**。

### 4.3 模型

我们评测四个模型：

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

将 4 个模型应用于 3,600 条 prompt request，共得到 **14,400 条模型响应**。

### 4.4 推理与评分

所有响应通过 OpenRouter 生成，推理参数为：

- `temperature = 0`
- `max_tokens = 150`

随后我们自动从输出中解析 `A/B/C/D`，并与 gold answer 比较，得到二元评分。14,400 条响应中只有 **3 条解析失败**，占比 **0.02%**，且全部来自 Llama 的安全拒答，因此对总体结论影响极小。

### 4.5 Bootstrap 分析

对每个数据集，我们进行 **2,000 次 bootstrap 重采样**。每次迭代都从该数据集对应题目中有放回抽样，并重新计算：

- prompt-specific accuracy
- prompt-averaged accuracy
- 模型间成对差值
- 各 prompt 下的模型排序

95% 置信区间由 bootstrap 分布的 2.5% 和 97.5% 分位数构造。

### 4.6 排名逆转率

我们将 `minimal_instruction` 作为 baseline prompt。对每次 bootstrap 迭代，我们比较其他 prompt 下的模型排序与 baseline 排序；只要顺序发生任何变化，就记为一次 ranking reversal。Ranking Reversal Rate（RRR）即发生 reversal 的迭代比例。

## 5. 主要结果

### 5.1 Prompt-averaged Accuracy

表 1 给出 prompt-averaged accuracy 及其 95% 置信区间。

| 数据集 | 模型 | 准确率 | 95% CI | 排名 |
| --- | --- | ---: | --- | ---: |
| ARC-Challenge | Gemini-2.0-flash | 94.00% | [91.42, 96.50] | 1 |
| ARC-Challenge | GPT-4o-mini | 90.83% | [87.58, 93.75] | 2 |
| ARC-Challenge | Qwen-2.5-7B | 85.08% | [81.17, 88.92] | 3 |
| ARC-Challenge | Llama-3.1-8B | 77.33% | [73.25, 82.00] | 4 |
| HellaSwag | GPT-4o-mini | 89.17% | [86.00, 92.09] | 1 |
| HellaSwag | Gemini-2.0-flash | 87.25% | [84.08, 90.25] | 2 |
| HellaSwag | Qwen-2.5-7B | 84.25% | [80.83, 87.75] | 3 |
| HellaSwag | Llama-3.1-8B | 68.33% | [63.92, 72.75] | 4 |
| MMLU | Gemini-2.0-flash | 85.08% | [81.17, 88.58] | 1 |
| MMLU | GPT-4o-mini | 73.42% | [68.67, 78.17] | 2 |
| MMLU | Qwen-2.5-7B | 70.33% | [65.58, 75.17] | 3 |
| MMLU | Llama-3.1-8B | 60.08% | [55.08, 65.25] | 4 |

从点估计上看，Gemini 在 ARC-Challenge 和 MMLU 上领先，而 GPT-4o-mini 在 HellaSwag 上领先。但这些“第一名”结论的稳固程度在不同 benchmark 上并不相同。

### 5.2 排名逆转率

表 2 给出相对于 minimal prompt 的 RRR。

| 数据集 | Benchmark | Natural | Order/Phrasing |
| --- | ---: | ---: | ---: |
| ARC-Challenge | 4.70% | 1.65% | 1.05% |
| HellaSwag | 62.55% | 41.35% | 38.50% |
| MMLU | 19.60% | 8.05% | 13.50% |

这个结果并不是“小幅且统一”的扰动。ARC-Challenge 极为稳定，MMLU 中等稳定，而 HellaSwag 明显更不稳定，在 benchmark-style prompt 下有超过六成的 bootstrap 迭代发生排名逆转。

### 5.3 成对显著性分析

成对 bootstrap 分析进一步揭示了不确定性集中在哪里：

- **ARC-Challenge**：所有成对比较都在 95% 水平上显著成立，这与极低的 RRR 一致。
- **HellaSwag**：GPT-4o-mini 相对 Gemini 的差值仅为 **1.92%**，95% CI 为 **[-0.67, 4.75]**，**p = 0.169**，因此头部两个模型并未显著分开。
- **HellaSwag**：Gemini 相对 Qwen 的差值为 **3.00%**，95% CI 为 **[-0.58, 6.42]**，**p = 0.102**，说明中间名次边界也不稳定。
- **MMLU**：Gemini 相对 GPT 的差值为 **11.67%**，95% CI 为 **[6.99, 16.08]**，显著成立。
- **MMLU**：GPT 相对 Qwen 的差值仅为 **3.08%**，95% CI 为 **[-1.50, 7.58]**，**p = 0.184**，因此第二、三名并未显著区分。

这些结果说明：当模型间差距较小时，排名不稳定性最容易出现。

## 6. 分数据集分析

### 6.1 ARC-Challenge：稳定的 leaderboard

ARC-Challenge 是本研究中最稳定的数据集。Gemini 在所有 prompt 下都保持领先，且所有成对差值都显著。极低的 RRR 说明 prompt 扰动和子集重采样不足以颠覆模型排序。

在当前实验设定下，ARC-Challenge 更像一个“宽间隔” benchmark，因此 leaderboard 基本可以被视为可靠的相对性能摘要。

### 6.2 HellaSwag：脆弱的榜首

HellaSwag 是对“静态 leaderboard 稳定”这一假设最直接的反例。虽然 GPT-4o-mini 的点估计最高，但它相对 Gemini 的优势并不显著；与此同时，HellaSwag 在所有非 baseline prompt 下都呈现最高的 RRR。

这意味着 HellaSwag 上的第一名并不稳固。尤其在 benchmark-style prompt 下，相对于 minimal prompt 的 reversal rate 达到 62.55%。因此，如果只基于单一 prompt 给出一个静态排行榜，就会高估排序结论的可靠性。

### 6.3 MMLU：榜首稳定，中游不稳

MMLU 呈现出一种混合模式。Gemini 明显领先，并在不同 prompt 下都保持第一；但 GPT-4o-mini 与 Qwen 并未显著分开，因此中间名次仍不完全稳定。

这说明一个 benchmark 可以同时满足两件事：榜首结论是稳固的，而非榜首名次依然具有结构性不确定性。

## 7. MMLU Subject 级分析

我们进一步对 MMLU 做了 subject-aware bootstrap 分析。

首先，pooled 与 stratified 的 full-MMLU bootstrap 都得到相同的总体排序：

- Gemini-2.0-flash > GPT-4o-mini > Qwen-2.5-7B > Llama-3.1-8B

这说明整体 MMLU 结论并不是“忽略 subject 结构”造成的假象。

其次，subject 级别的不稳定性差异很大。非 minimal prompt 下的平均 RRR 分别为：

- philosophy: 67.93%
- high_school_physics: 62.25%
- college_medicine: 51.55%
- international_law: 45.48%
- formal_logic: 37.82%
- high_school_macroeconomics: 14.50%

因此，即使一个 benchmark 在整体上看只是“中等不稳定”，其内部不同 subject 也可能呈现非常不同的排名稳定性。

## 8. 讨论

本文结果支持三个判断。

第一，prompt 敏感性不能只理解为分数波动。在某些任务上，这种波动已经大到足以改变模型的相对排序，而排序往往才是更重要的决策对象。

第二，单一 prompt 的评测过于狭窄。特别是在 HellaSwag 上，如果不显式考虑 prompt 与样本扰动，就容易把“当前设定下略高的点估计”误读为“稳健的第一名”。

第三，仅报告准确率置信区间还不够。模型比较真正关心的问题是排序是否稳，而不仅是期望分数是否不同。RRR 和 rank probability 能把这种排序不确定性直接展示出来。

## 9. 局限性

本研究有几个明确局限。

第一，我们只评测了三个多项选择 benchmark，因此结论不应外推到所有 LLM 任务。

第二，我们只比较了四个模型。若模型集合更大，排名结构可能更复杂。

第三，我们的 prompt 扰动是浅层且 task-preserving 的，只覆盖了 prompt 设计空间中的一个重要子集。

第四，当前仓库中的完整 Phase 2 结果历史上首先来自 notebook 运行，之后才与脚本口径完全对齐。虽然仓库现已标准化，但这一历史事实仍应在报告中说明。

## 10. 结论

本文讨论的问题是：如果换一种问法，LLM 排名会改变吗？答案是：会，但不是所有 benchmark 都同样严重。

ARC-Challenge 的排行榜高度稳定。MMLU 的榜首稳定，但中游名次仍有不确定性。HellaSwag 对 prompt 和子集变化明显更敏感，其表面上的第一名并未显著领先第二名。

因此，benchmark 分数不应被自动理解为稳定的模型排序。更可靠的评测实践应当同时报告“谁平均表现最好”以及“这个排序在 prompt 与样本变化下是否稳健”。

## 参考文献

- Clark, P., Cowhey, I., Etzioni, O., Khot, T., Sabharwal, A., Schoenick, C., and Tafjord, O. 2018. *Think You Have Solved Question Answering? Try ARC, the AI2 Reasoning Challenge.*
- Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., and Steinhardt, J. 2020. *Measuring Massive Multitask Language Understanding.*
- Zellers, R., Holtzman, A., Bisk, Y., Farhadi, A., and Choi, Y. 2019. *HellaSwag: Can a Machine Really Finish Your Sentence?*
- Zhu, K., Wang, J., Zhou, J., Wang, Z., Chen, H., Wang, Y., Yang, L., Ye, W., Gong, N. Z., Zhang, Y., and Xie, X. 2023. *PromptRobust: Towards Evaluating the Robustness of Large Language Models on Adversarial Prompts.*

## 附录 A. 复现说明

- 统一入口：`run_pipeline.py`
- Phase 1：`src/01_data_prep.py`
- Phase 2：`src/02_api_runner.py`
- Phase 3：`src/03_scorer.py`
- Phase 4：`src/04_analysis.py`、`src/04_mmlu_subject_bootstrap.py`
- 主结果表格：`data/04_analysis/`
- 主图表：`plots/`

## 附录 B. 图表

### B.1 Bootstrap 准确率箱线图

![Accuracy Boxplots](../plots/accuracy_boxplots.png)

### B.2 排名逆转率

![Ranking Reversal Rate](../plots/ranking_reversal_rate.png)
