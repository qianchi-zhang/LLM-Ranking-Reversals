# 复现说明

## 1. 环境要求

- Python 3.11
- `pip install -r requirements.txt`

推荐使用隔离环境，例如：

```bash
conda create -n llm-ranking-env python=3.11 -y
conda activate llm-ranking-env
pip install -r requirements.txt
```

## 2. API Key

Phase 2 需要 `OPENROUTER_API_KEY`。

在仓库根目录创建 `my.env` 或 `.env`：

```text
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
```

## 3. 最快复现方式

推荐直接使用统一入口 [run_pipeline.py](/d:/ST5230/LLM-Ranking-Reversals/run_pipeline.py)。

### 全量运行

```bash
python run_pipeline.py --mode full --overwrite
```

### 小样本试跑

```bash
python run_pipeline.py --mode pilot --limit 50 --overwrite
```

### 从 Phase 2 继续

```bash
python run_pipeline.py --start-phase 2 --mode full --resume
```

### 只重跑分析

```bash
python run_pipeline.py --start-phase 3 --end-phase 4
```

### 跳过 MMLU subject 分析

```bash
python run_pipeline.py --start-phase 4 --end-phase 4 --skip-mmlu-subject-bootstrap
```

## 4. 分阶段复现

### Step 1: 生成题目与 Prompt

```bash
python src/01_data_prep.py
```

预期输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Step 2: 调用模型

```bash
python src/02_api_runner.py --mode full --overwrite
```

可选：

```bash
python src/02_api_runner.py --mode pilot --limit 50 --overwrite
python src/02_api_runner.py --mode full --resume
```

真实运行口径：

- 输入：`data/01_prompts.jsonl`
- Prompt 来源：`messages[0].content`
- 模型：
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

### Step 3: 解析与评分

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

## 5. 当前结果规模检查

当前 `develop` 分支对应的完整结果规模为：

- 900 道原始题目
- 3600 条 prompt request
- 14400 条模型结果

如果你的结果明显少于这个规模，优先检查：

- 是否误用了 `pilot` 模式
- 是否只跑了部分模型
- 是否输出文件被中断或覆盖

## 6. 脚本与 Notebook 的角色

- `src/02_api_runner.py` 是当前标准化后的脚本复现入口
- `run_pipeline.py` 是当前标准化后的统一总入口
- `src/02_api_runner.ipynb` 作为交互式测试与探索 notebook 保留

如果 notebook、脚本和文档出现口径冲突，应优先保证脚本入口与 README 的复现说明一致。
