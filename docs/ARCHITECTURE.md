# 项目架构说明

## 1. 目标

本文档说明仓库当前的标准化架构，以及不同目录在项目中的职责边界。它面向维护者和复现者，回答两个问题：

- 这个仓库的标准运行入口是什么
- 代码、数据、图表、报告和历史材料分别放在哪里

## 2. 架构分层

### 编排层

- `run_pipeline.py`

职责：

- 串联 Phase 1 到 Phase 4
- 作为默认复现入口
- 统一管理分阶段重跑和 Phase 2 参数透传

### 代码层

- `src/`

职责：

- 数据抽样与 prompt 生成
- OpenRouter 模型推理
- 响应解析与评分
- 基于固定评分结果的重抽样分析与可视化

约束：

- `src/` 只放当前标准实验逻辑
- 历史脚本放在 `src/legacy/`
- `src/02_api_runner.ipynb` 保留为交互式补充材料，不是默认入口

### 数据层

- `data/`

职责：

- 保存题目样本
- 保存 prompt 请求
- 保存原始模型响应
- 保存评分结果
- 保存分析阶段生成的表格

当前标准化数据路径：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`
- `data/02_raw_responses.jsonl`
- `data/02_raw_responses.csv`
- `data/03_scored/`
- `data/04_analysis/`
- `data/04_mmlu_subject_analysis_expanded/`

说明：

- `data/04_mmlu_subject_analysis/` 是较早保留产物
- 当前扩展 MMLU 学科分析的标准输出路径是 `data/04_mmlu_subject_analysis_expanded/`

### 可视化层

- `plots/`

职责：

- 保存最终图表
- 供报告和 presentation 直接引用

### 报告层

- `reports/`

职责：

- 保存 Markdown 分析说明
- 保存 final report 源文件
- 保存 Beamer slides 与 HTML slides
- 保存可直接分发的 zip/pdf 交付件

当前权威路径：

- 最终报告：`reports/final_report/final_report.tex`
- 最终 slides：`reports/overleaf_package/presentation.tex`
- HTML 展示：`reports/web_presentation/index.html`

### 文档层

- `docs/`

职责：

- 保存架构说明
- 保存复现说明
- 保存历史规划与课程归档

子目录：

- `docs/history/`：计划、日志、过程记录
- `docs/archive/`：proposal、反馈、课程归档材料

## 3. 四阶段映射

### Phase 1

- 脚本：`src/01_data_prep.py`
- 输入：Hugging Face benchmark 数据集
- 输出：`data/00_raw_question.jsonl`、`data/01_prompts.jsonl`

### Phase 2

- 脚本：`src/02_api_runner.py`
- 补充 notebook：`src/02_api_runner.ipynb`
- 输入：`data/01_prompts.jsonl`
- 输出：`data/02_raw_responses.jsonl`、`data/02_raw_responses.csv`

### Phase 3

- 脚本：`src/03_scorer.py`
- 输入：`data/02_raw_responses.csv`
- 输出：`data/03_scored/`

### Phase 4

- 主脚本：`src/04_analysis.py`
- 扩展脚本：`src/04_mmlu_subject_bootstrap.py`
- 输入：`data/03_scored/scored_results.csv` 以及扩展 MMLU 响应文件
- 输出：`data/04_analysis/`、`data/04_mmlu_subject_analysis_expanded/`、`plots/`、`reports/`

说明：

- Phase 4 不重新调用 API
- 所有 accuracy、PRRR、SRRR 和 rank probability 统计量都基于固定评分结果
- 重抽样单位是题目子集，而不是新的模型请求

## 4. 当前实验口径

主标准化实验：

- 900 道题
- 3600 条 prompt requests
- 14400 条模型 responses

扩展 MMLU 学科实验：

- 5 个 subject
- 每个 subject 200 道题
- 16000 条额外 responses

当前真实模型集合：

- `openai/gpt-4o-mini`
- `google/gemini-2.0-flash-001`
- `qwen/qwen-2.5-7b-instruct`
- `meta-llama/llama-3.1-8b-instruct`

## 5. 标准化规则

### 命名规则

- 阶段脚本使用数字前缀：`01_`、`02_`、`03_`、`04_`
- 数据目录按阶段编号组织
- 文档、报告和代码分层存放

### 入口规则

- 默认复现入口是 `run_pipeline.py`
- 分阶段脚本保留，便于局部重跑
- notebook 保留，但不应替代标准脚本入口

### 一致性规则

- 修改输入输出路径时，必须检查下游脚本
- 修改目录结构后，必须同步更新 README、`docs/REPRODUCIBILITY.md` 和 `AGENTS.md`
- 如果历史文件和当前实现冲突，应优先相信当前脚本和当前产物
