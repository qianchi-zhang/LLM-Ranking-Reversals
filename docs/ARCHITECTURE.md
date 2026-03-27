# 项目架构说明

## 1. 目标

本文件用于说明本仓库的标准化逻辑架构，帮助后续开发者快速区分：

- 哪些文件是代码
- 哪些文件是实验产物
- 哪些文件是图表与报告
- 哪些文件是历史计划文档

## 2. 分层结构

### 代码层

目录：

- `src/`

职责：

- 数据抽样
- Prompt 构造
- 模型调用
- 结果打分
- Bootstrap 统计分析

原则：

- `src/` 中只放可执行实验逻辑
- 不把报告讨论写进 `src/`

### 数据层

目录：

- `data/`

职责：

- 原始抽样题目
- Prompt 请求
- 模型原始响应
- 打分结果
- 统计分析表

当前分层：

- `data/00_raw_question.jsonl`
- `data/01_prompts.jsonl`
- `data/02_raw_responses.*`
- `data/03_scored/`
- `data/04_analysis/`
- `data/04_mmlu_subject_analysis/`

原则：

- `data/` 中只放数据和结果表
- 不把代码放进 `data/`

### 可视化层

目录：

- `plots/`

职责：

- 保存论文/报告中可直接引用的图像文件

### 报告层

目录：

- `reports/`

职责：

- 保存分析摘要
- 保存研究问题讨论
- 保存 MMLU subject 分析说明

### 文档层

目录：

- `docs/`

职责：

- 保存架构说明
- 保存复现说明
- 保存标准化规范

### 历史参考层

文件：

- `PROJECT_PLAN.md`
- `PROJECT_LOG.md`
- `TECH_STACK.md`
- proposal PDF

职责：

- 记录项目早期计划与开发过程

注意：

- 它们不一定反映当前真实实现
- 当前真实实现以 `src/`、`data/`、`reports/` 为准

## 3. 四阶段流水线映射

### Phase 1

- 代码：`src/01_data_prep.py`
- 输出：`data/00_raw_question.jsonl`、`data/01_prompts.jsonl`

### Phase 2

- 代码：`src/02_api_runner.py`
- 历史运行入口：`src/02_api_runner.ipynb`
- 输出：`data/02_raw_responses.jsonl`、`data/02_raw_responses.csv`

### Phase 3

- 代码：`src/03_scorer.py`
- 输出：`data/03_scored/`

### Phase 4

- 代码：`src/04_analysis.py`
- 补充代码：`src/04_mmlu_subject_bootstrap.py`
- 输出：`data/04_analysis/`、`data/04_mmlu_subject_analysis/`、`plots/`、`reports/`

## 4. 当前标准化约定

### 命名约定

- 阶段脚本采用编号前缀：`01_`、`02_`、`03_`、`04_`
- 数据产物目录按阶段编号组织
- 报告与图表目录不再混放代码

### 变更约定

- 修改上游数据结构时，必须同步检查下游阶段
- 默认不覆盖已有实验产物
- 新的规范说明优先补到 `docs/`

## 5. 当前最重要的事实

- 当前仓库已经有完整实验结果
- 当前实际模型集合不包含 Claude
- 当前 Phase 2 已产出结果来自 notebook 全量运行
- 当前脚本版 `src/02_api_runner.py` 已对齐 notebook 口径，作为后续标准复现入口
