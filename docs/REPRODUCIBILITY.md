# 复现说明

## 1. 环境要求

- Python 3.11
- `pip install -r requirements.txt`

推荐使用独立环境，例如：

```bash
conda create -n llm-ranking-env python=3.11 -y
conda activate llm-ranking-env
pip install -r requirements.txt
```

## 2. API Key

Phase 2 需要 `OPENROUTER_API_KEY`。

当前项目兼容两种本地配置文件：

- `my.env`
- `.env`

格式：

```text
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
```

## 3. 标准复现顺序

### Step 1: 生成题目与 Prompt

```bash
python src/01_data_prep.py
```

预期输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Step 2: 调用模型

当前标准复现入口：

```bash
python src/02_api_runner.py --mode full --overwrite
```

如果只想做小样本检查：

```bash
python src/02_api_runner.py --mode pilot --limit 50 --overwrite
```

如果运行中断后继续：

```bash
python src/02_api_runner.py --mode full --resume
```

真实实验口径：

- 输入：`data/01_prompts.jsonl`
- Prompt 来源：`messages[0].content`
- 模型集合：
  - `openai/gpt-4o-mini`
  - `google/gemini-2.0-flash-001`
  - `qwen/qwen-2.5-7b-instruct`
  - `meta-llama/llama-3.1-8b-instruct`
- 解码参数：
  - `temperature=0`
  - `max_tokens=150`

预期输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

### Step 3: 打分

```bash
python src/03_scorer.py
```

预期输出：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Step 4: 主分析

```bash
python src/04_analysis.py
```

预期输出：

- `data/04_analysis/`
- `plots/accuracy_boxplots.png`
- `plots/ranking_reversal_rate.png`
- `plots/*_rank_probability_heatmaps.png`
- `reports/analysis_summary.md`

### Step 5: MMLU Subject 分析

```bash
python src/04_mmlu_subject_bootstrap.py
```

预期输出：

- `data/04_mmlu_subject_analysis/`
- `plots/mmlu_subject_accuracy.png`
- `plots/mmlu_subject_rrr.png`
- `reports/mmlu_subject_bootstrap_summary.md`

## 4. 当前仓库中已存在的结果规模

当前 `develop` 分支的已提交结果对应规模为：

- 900 条原始题目
- 3600 条 prompt request
- 14400 条模型评分结果

如果你的结果规模明显低于这个数量，优先检查：

- 是否误用了 `pilot` 模式
- 是否忘记关闭旧的 `[:50]` 试跑逻辑
- 是否输出文件被中断或重复覆盖

## 5. Notebook 与脚本的关系

- `src/02_api_runner.ipynb` 是历史上实际跑出当前结果的入口
- `src/02_api_runner.py` 是当前标准化后的脚本复现入口

如果两者口径发生冲突，优先保证：

1. 当前脚本与已提交结果口径一致
2. README 与 docs 中的说明同步更新

## 6. 复现检查清单

在宣称“已成功复现”之前，建议至少核对：

- `data/01_prompts.jsonl` 行数是否为 3600
- `data/03_scored/scored_results.csv` 是否约为 14400 条结果
- `reports/analysis_summary.md` 是否成功生成
- `plots/` 中的主图是否成功生成
