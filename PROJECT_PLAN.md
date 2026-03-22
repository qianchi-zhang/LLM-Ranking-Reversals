# 🚀 ST5230 Project Execution Plan: LLM Ranking Reversals

**Project Title:** Do LLM Rankings Change if You Ask Differently? Evaluating LLM Ranking Reversals Under Prompt Perturbations
**Team (Group 14):** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

---

## 1. 总体架构与数据流 (Architecture & Data Pipeline)

整个实验流水线分为四个独立解耦的阶段。数据必须以标准化的格式（如 JSONL）在各个阶段之间单向流动，以保证完全的可复现性。

* **Phase 1: Data & Prompt Engine (数据与提示词引擎)**

  * **输入:** HuggingFace 上的原始数据集（MMLU, ARC-Challenge, HellaSwag）。
  * **处理:** 按照分层抽样（Stratified Sampling）各自抽取 300 题（共 900 题）。将每道题与 4 种不同的 Prompt 模板结合。
  * **输出:** `master_prompts.jsonl` (包含：`task_id`, `dataset`, `prompt_type`, `full_text`, `gold_label`)。
* **Phase 2: OpenRouter API Orchestrator (API 调度器)**

  * **输入:** `master_prompts.jsonl`。
  * **处理:** 使用统一的参数（Temperature=0, Top_p=1）并发调用 4 个大模型。添加异常捕获和速率限制（Rate-limit）处理。
  * **输出:** `raw_responses.jsonl` (追加字段：`model_id`, `raw_output`, `timestamp`)。
* **Phase 3: Parser & Scorer (解析与评分器)**

  * **输入:** `raw_responses.jsonl`。
  * **处理:** 编写正则表达式，从模型长短不一的回答中精确提取 A/B/C/D 选项，并与 `gold_label` 对比。
  * **输出:** `scored_results.csv` (二值化评分：1 代表正确，0 代表错误)。
*  ### Phase 4: 统计分析与可视化 (`04_analysis.ipynb`)

  **负责人:** 张千驰 (ZHANG QIANCHI - P4)
  **目标:** 处理二元评分数据，通过 Bootstrap 重采样量化评估的不确定性和排名不稳定性。

  #### 1. 数据加载与预处理


  * **输入:** `data/03_scored/scored_results.csv` (预期包含列: `task_id`, `dataset`, `prompt_type`, `model_id`, `score`).
  * **逻辑:**
    * 加载数据并清除空值（过滤掉 API 调用或解析失败的行）。
    * 按 `dataset`（如 MMLU, ARC, HellaSwag）进行分组，确保每个任务的分析是独立的。
    * 计算每个“模型-提示词”组合的**点估计准确率**（即常规的平均准确率），作为我们比较的基准。

  #### 2. Bootstrap 重采样引擎

  * **逻辑:** 通过有放回抽样来模拟数据集的方差。
  * **实现:**
    * 针对每个 `dataset`（N=300 题），进行**有放回**的 N 次抽样，构建一个 Bootstrap 子集。
    * 在这个特定子集上，计算 4 个模型在 4 种提示词变体下的平均准确率。
    * 重复此过程 r=100 次（在跑最终报告时建议调大至 r=1000 次）。
  * **数据结构:** 生成一个形状为 `(r_iterations, num_models, num_prompts)` 的 3D 矩阵/张量。

  #### 3. 置信区间 (CI) 计算

  * **逻辑:** 为我们的点估计准确率加上统计学上的“误差棒”。
  * **实现:**
    * 对步骤 2 中生成的重采样准确率分布应用 `numpy.percentile()`。
    * 提取 2.5%（下界）和 97.5%（上界）的分位数，构建严谨的 **95% 置信区间**。

  #### 4. 排名逆转率 (RRR - Ranking Reversal Rate)

  * **基准定义:** 在每一次重采样迭代中，将模型在“极简指令 (Minimal Instruction)”提示词下的表现排名定义为基准排名向量 R_base（例如：[GPT=1, Llama=2, Claude=3, Gemini=4]）。
  * **对比计算:**
    * 计算在同一次迭代中，其余 3 种提示词变体下的排名向量 R_variant。
    * **条件判断:** 如果 R_variant != R_base（意味着至少有一个模型互换了位置），则标记为一次逆转。
  * **最终指标:** 计算在这 r 次重采样迭代中，发生逆转的次数所占的百分比。

  #### 5. 学术级数据可视化

  * **图表 A: 准确率箱线图 (Accuracy Boxplots)**
    * *坐标轴:* X = 提示词模板, Y = 准确率 (%)。
    * *颜色分类:* 4 个模型。
    * *目的:* 直观展示哪个模型表现出最大的方差，对提示词变化最敏感（箱体越长，代表越不稳定）。
  * **图表 B: 排名概率热力图 (Rank Probability Heatmap)**
    * *坐标轴:* X = 排名位置 (第1名, 第2名, 第3名, 第4名), Y = 4 个模型。
    * *数值:* 模型在所有 Bootstrap 迭代中落在该特定排名的概率 (0-100%)。
    * *目的:* 证明所谓的“第一名”模型在统计上是否真的稳固，还是说它因为提示词噪音有很高的概率掉分排名下滑。

---

## 2. 团队分工 (Role Assignments)

| 角色 / 负责人               | 核心职责                                                                          | 交付物                                        |
| :-------------------------- | :-------------------------------------------------------------------------------- | :-------------------------------------------- |
| **P1: Data Engineer** | 负责下载和清洗数据集。设计严格的 4 种 Prompt 模板代码实现。                       | `01_data_prep.py<br>``master_prompts.jsonl` |
| **P2: API Architect** | 封装 OpenRouter 调用逻辑，处理 4 个模型的推理。确保 14,400 次 API 调用稳定跑完。  | `02_api_runner.py<br>``raw_responses.jsonl` |
| **P3: Eval Scorer**   | 负责最“脏”的活：写正则提取答案。处理模型不按指令输出的 Edge Cases。             | `03_scorer.py<br>``scored_results.csv`      |
| **P4: Statistician**  | 编写 Bootstrap 重采样脚本，计算统计显著性。绘制用于 Final Report 的所有高级图表。 | `04_analysis.ipynb<br>``plots/*.pdf`        |

---

## 3. 实验细节规范 (Experimental Protocols)

### 3.1 提示词模板设计 (Prompt Perturbations)

对于每一道题目，必须严格生成以下 4 个变体：

1. **Minimal Instruction:** 极简零样本（Zero-shot）。
   * *例:* `[Question] \nOptions: [A/B/C/D]. Answer with one option only.`
2. **Benchmark-style Instruction:** 标准格式化指令。
   * *例:* `Please read the following question and select the correct option. \nQuestion: [Question] \nChoices: [A/B/C/D] \nOutput only the letter corresponding to the correct answer.`
3. **Minor Non-semantic Variations:** 非语义微小扰动（标点/换行符/大小写）。
   * *例:* 使用 `---` 替代 `\n`，或者将 `Options:` 改为 `options - `。
4. **Order/Phrasing Variation:** 顺序/措辞变化。
   * *例:* 将格式要求放在问题之前：`Answer with exactly one letter. Here is the question: [Question] \n[A/B/C/D]`

### 3.2 OpenRouter 模型映射

必须在代码中锁定固定的 Model ID，防止 API 后台静默更新导致结果不可复现：

* GPT-4o Mini: `openai/gpt-4o-mini`
* Claude 3.5 Haiku: `anthropic/claude-3.5-haiku`
* Gemini 2.0 Flash: `google/gemini-2.0-flash-001`
* Llama 3.1 8B: `meta-llama/llama-3.1-8b-instruct`

### 3.3 统计方法学 (Statistical Methodology)

在 Jupyter Notebook 中，P4 需要实现以下数学逻辑：

* **Bootstrap 均值与 CI**:
  从 n=300 的样本中，有放回地抽样 n 次，形成一个子集。重复 r=100 次。计算经验分布的 2.5% 和 97.5% 分位数作为 95% CI。
* **排名逆转率 (Ranking Reversal Rate, RRR)**:
  设基准排名为使用 Minimal prompt 时的模型排名向量 R_base。对于任意其他配置 c (不同的 prompt 或子集)，计算其排名向量 R_c。统计排名发生变化的频率。

---

## 4. 协作纪律与 Git 规范 (Collaboration Rules)

1. **脱敏原则**: 绝对不允许将带有 API Key 的 `.env` 文件 Push 到 GitHub。使用 `os.environ.get("OPENROUTER_API_KEY")` 读取环境变量。
2. **数据版本控制**: `raw_responses` 和 `scored_results` 等数据文件（CSV/JSONL）建议通过 OneDrive 或 Google Drive 共享，GitHub 只负责追踪代码和生成的图表。
3. **开发环境**: 统一使用 Python 3.10+。项目根目录必须包含 `requirements.txt` (包含 `pandas`, `requests`, `matplotlib`, `seaborn`, `scipy` 等核心库)。

---

## 5. 项目推进时间表 (Timeline)

* **Week 1 (环境搭建 & 小样测试):**
  * P1 完成 3 个数据集的 900 题抽取和 4 种 Prompt 的生成。
  * P2 完成 OpenRouter API 脚本，抽取 10 道题跑通 4 个模型。
* **Week 2 (全量跑批 & 解析):**
  * P2 运行全量数据：900 questions × 4 prompts × 4 models = 14,400 次 API 调用。
  * P3 拿到数据，写正则并校验，生成最终的准确率打分表。
* **Week 3 (数据分析 & 绘图):**
  * P4 执行 Bootstrap，输出 Boxplots 和 Pairwise Ranking Heatmaps。
  * 全员开会 review 跑出的结论是否与假设相符。
* **Week 4 (报告撰写):**
  * 将图表和结论填入 Overleaf LaTeX 模板，完成 8-10 页的最终报告。
