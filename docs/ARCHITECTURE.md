# 项目架构说明

## 1. 目标

本文件用于说明仓库的标准化结构，以及不同目录在项目中的职责边界。

## 2. 架构分层

### 编排层

- `run_pipeline.py`

职责：

- 串联 `01 -> 04` 阶段；
- 作为默认复现入口；
- 统一管理部分重跑和 Phase 2 参数传递。

### 代码层

- `src/`

职责：

- 数据抽样与 prompt 生成；
- OpenRouter 模型调用；
- 答案解析与评分；
- 基于固定评分结果的重抽样分析与可视化生成。

约束：

- `src/` 只放可执行实验逻辑；
- 历史脚本放 `src/legacy/`，不混入主流水线。

### 数据层

- `data/`

职责：

- 保存原始题目样本；
- 保存 prompt 请求；
- 保存模型原始响应；
- 保存评分结果；
- 保存分析阶段生成的表格。

当前阶段化目录：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`
- `data/02_raw_responses.*`
- `data/03_scored/`
- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`

### 可视化层

- `plots/`

职责：

- 保存最终图表；
- 供报告和汇报材料直接引用。

### 报告层

- `reports/`

职责：

- 保存分析总结；
- 保存研究问题讨论；
- 保存 MMLU subject 分析说明。

### 文档层

- `docs/`

职责：

- 保存架构说明；
- 保存复现说明；
- 保存历史计划与归档材料。

子目录：

- `docs/history/`：历史计划、日志、技术记录
- `docs/archive/`：proposal、feedback 等归档材料

## 3. 四阶段映射

### Phase 1

- 脚本：`src/01_data_prep.py`
- 输入：HuggingFace benchmark 数据集
- 输出：`data/00_raw_question.jsonl`、`data/01_prompts.jsonl`

### Phase 2

- 脚本：`src/02_api_runner.py`
- 辅助 notebook：`src/02_api_runner.ipynb`（交互式测试与探索）
- 输入：`data/01_prompts.jsonl`
- 输出：`data/02_raw_responses.jsonl`、`data/02_raw_responses.csv`

### Phase 3

- 脚本：`src/03_scorer.py`
- 输入：`data/02_raw_responses.csv`
- 输出：`data/03_scored/`

### Phase 4

- 脚本：`src/04_analysis.py`
- 补充脚本：`src/04_mmlu_subject_bootstrap.py`
- 输入：`data/03_scored/scored_results.csv`
- 输出：`data/04_analysis/`、`data/04_mmlu_subject_analysis/`、`plots/`、`reports/`

说明：

- Phase 4 不重新调用 API；
- 所有 accuracy、PRRR、SRRR 统计量都直接复用 Phase 3 生成的固定 `score`；
- 重抽样单位是题目子集，而不是新的模型请求。

## 4. 标准化规则

### 命名规则

- 阶段脚本使用数字前缀：`01_`、`02_`、`03_`、`04_`
- 数据目录按阶段编号组织
- 文档与报告目录不混放代码

### 入口规则

- 默认复现入口是 `run_pipeline.py`
- 分阶段脚本继续保留，便于局部重跑和调试
- 辅助 notebook 保留用于交互式测试与探索，标准复现入口仍然是脚本

### 一致性规则

- 修改某阶段输入输出格式时，必须同步检查下游脚本
- 修改项目结构后，必须同步更新 README、复现文档和 AGENTS

## 5. 真实口径说明

- 当前仓库已经包含完整实验产物；
- 当前真实模型集合是 `GPT-4o-mini / Gemini-2.0-flash / Qwen-2.5-7B / Llama-3.1-8B`；
- 历史文档中提到的 Claude 等旧方案只代表早期计划，不代表最终实现。
