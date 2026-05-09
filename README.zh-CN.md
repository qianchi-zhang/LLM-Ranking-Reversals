# LLM Ranking Reversals

[English](README.md) | [中文](README.zh-CN.md)

**第 14 组成员：** ZHANG QIANCHI，PENG YANGYUNZHI，JIANG YIFAN，MENG XIANGCHEN

## 项目概述

本仓库研究的是：当评测协议发生轻微但有意义的变化时，LLM benchmark leaderboard 的模型排序是否仍然稳定。项目重点分离两类不稳定来源：

- 非语义 prompt 变化
- 评测子集变化
- 由此引发的模型排名反转

主要结论具有明显的 benchmark 依赖性。ARC-Challenge 相对稳定，MMLU 在整体层面中等稳定但在更细粒度学科切片上更脆弱，HellaSwag 则明显更容易发生排名反转。因此，本仓库把 ranking robustness 视为与 average accuracy 同等重要的评测对象。

## 仓库定位

这是一个已经完成主实验并保留完整成果的实验仓库，不是项目骨架。仓库中已经包含：

- 标准化后的流水线代码
- 已生成的实验产物
- 分析表格与图表
- 报告与展示源码
- 历史规划与课程归档材料

当前默认主分支是 `main`。

## 权威入口

| 用途 | 权威路径 |
| --- | --- |
| 端到端统一入口 | `run_pipeline.py` |
| Phase 2 标准脚本入口 | `src/02_api_runner.py` |
| 最终 slides 源文件 | `reports/overleaf_package/presentation.tex` |
| 最终报告源文件 | `reports/final_report/final_report.tex` |

可选但非默认入口：

- `src/02_api_runner.ipynb`：交互式 notebook 补充材料，不是默认复现入口
- `docs/history/`：计划与过程历史
- `docs/archive/`：课程归档文件与反馈材料

## 仓库结构

```text
LLM-Ranking-Reversals/
|-- run_pipeline.py
|-- src/
|   |-- 01_data_prep.py
|   |-- 01_data_prep_MMLU_subject.py
|   |-- 02_api_runner.py
|   |-- 02_api_runner.ipynb
|   |-- 03_scorer.py
|   |-- 04_analysis.py
|   |-- 04_mmlu_subject_bootstrap.py
|   `-- legacy/
|-- data/
|   |-- 00_raw_question*.jsonl
|   |-- 01_prompts*.jsonl
|   |-- 02_raw_responses*.jsonl / *.csv
|   |-- 03_scored/
|   |-- 04_analysis/
|   |-- 04_mmlu_subject_analysis/
|   `-- 04_mmlu_subject_analysis_expanded/
|-- plots/
|-- reports/
|   |-- final_report/
|   |-- overleaf_package/
|   |-- web_presentation/
|   `-- README.md
|-- docs/
|   |-- ARCHITECTURE.md
|   |-- REPRODUCIBILITY.md
|   |-- history/
|   `-- archive/
|-- AGENTS.md
|-- requirements.txt
`-- my.env
```

## 最短复现路径

推荐 Python 版本：`3.11`

```bash
pip install -r requirements.txt
```

将真实 `OPENROUTER_API_KEY` 放在以下任一位置：

1. `my.env.local`，最适合本地私有使用
2. `.env`
3. 本地修改后的 `my.env`

然后运行：

```bash
python run_pipeline.py --mode full --overwrite
```

常用变体：

```bash
python run_pipeline.py --mode pilot --limit 50 --overwrite
python run_pipeline.py --start-phase 2 --mode full --resume
python run_pipeline.py --start-phase 3 --end-phase 4
python run_pipeline.py --start-phase 4 --end-phase 4 --skip-mmlu-subject-bootstrap
```

## 四阶段流水线

### Phase 1：数据准备

```bash
python src/01_data_prep.py
```

主要输出：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`

### Phase 2：模型推理

```bash
python src/02_api_runner.py --mode full --overwrite
```

主要输出：

- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`

`src/02_api_runner.py` 是标准脚本复现路径。`src/02_api_runner.ipynb` 仅作为交互式检查和探索性运行的补充材料保留。

### Phase 3：解析与评分

```bash
python src/03_scorer.py
```

主要输出：

- `data/03_scored/scored_results.csv`
- `data/03_scored/parse_failures.csv`

### Phase 4：重抽样分析

```bash
python src/04_analysis.py
python src/04_mmlu_subject_bootstrap.py
```

主要输出：

- `data/04_analysis/`
- `data/04_mmlu_subject_analysis_expanded/`
- `plots/`
- `reports/`

Phase 4 完全在本地进行。它复用固定评分结果，计算 accuracy、PRRR、SRRR、置信区间以及 rank probability 等统计量，不会再次调用 API。

## 当前实验口径

- 主标准化 benchmark pool：900 道题
- 主实验 prompt requests：3600 条
- 主实验模型 responses：14400 条
- 扩展 MMLU 学科实验：5 个 subject，每个 200 题，共 16000 条额外 responses

Prompt 模板：

- `minimal_instruction`
- `benchmark_style`
- `natural_style`
- `order_phrasing_variation`

模型集合：

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

解码设置：

- `temperature=0`
- `max_tokens=150`

## 结果与报告入口

如果你只想看最终成果，建议从这里开始：

- `reports/final_report/final_report.tex`：最终报告权威源文件
- `reports/overleaf_package/presentation.tex`：最终 Beamer slides 权威源文件
- `reports/overleaf_package/presentation.pdf`：已编译展示版本
- `reports/web_presentation/index.html`：HTML 演示版本
- `reports/README.md`：报告与展示材料索引

重要分析产物：

- `reports/analysis_summary.md`
- `reports/focused_research_question_discussion.md`
- `reports/conference_style_report_en.md`
- `plots/`
- `data/04_analysis/`
- `data/04_mmlu_subject_analysis_expanded/`

## 文档阅读顺序

1. `README.md`
2. `README.zh-CN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/REPRODUCIBILITY.md`
5. `AGENTS.md`
6. `reports/README.md`

## 历史材料与归档

- `docs/history/` 保存项目规划、过程记录和历史说明。
- `docs/archive/` 保存课程 proposal、反馈等归档文件。
- `reports/final_report/archive/` 保存非权威 final report 变体，供追溯参考。

如果历史文档与当前实现不一致，应优先以 `run_pipeline.py`、`src/`、`data/`、`plots/` 和 `docs/` 下的标准化文档为准。

## 凭证与安全

- 被跟踪的 `my.env` 只是占位符模板，不包含真实凭证。
- 不要提交真实 `OPENROUTER_API_KEY`。
- 本地私有凭证优先放在 `my.env.local`、`.env`，或通过 `--env-file` 显式指定。
