# 📝 Project Log: Group 14 - LLM Ranking Reversals

> **项目说明**：本文件用于实时记录 ST5230 课程项目的开发进度、关键决策及团队分工。每位成员在完成阶段性任务或遇到重大 Bug 时请在此更新。

---

## 📊 总体进度看板

| 阶段                                | 状态      | 负责人     | 预期完成时间 |
| :---------------------------------- | :-------- | :--------- | :----------- |
| **Phase 1: 数据与提示词工程** | ⏳ 进行中 | 彭 (Peng)  | 2026-03-23   |
| **Phase 2: API 调度与跑批**   | ⏳ 进行中 | 江 (Jiang) | 2026-03-23   |
| **Phase 3: 统计分析与建模**   | 📅 待启动 | 孟 (Meng)  | 2026-03-23   |
| **Phase 4: 结果评分与解析**   | 📅 待启动 | 张 (Zhang) | 2026-03-23   |

---

## 🚀 72小时冲刺：小样跑通计划 (Pilot Run)

**目标**：在 3 天内完成 15 道题（3个数据集 $\times$ 5题）的全流程自动化测试，确保 Pipeline 无 Bug。

### 👤 彭 (P1 - Data & Prompt Engineer)

**AI 助手指令：** "请帮我编写 `src/01_data_prep.py`。任务包括：使用 `datasets` 库从 HuggingFace 载入 MMLU-STEM、ARC-Challenge 和 HellaSwag；每个数据集随机抽取 5 题并固定随机种子 42；为每题生成 4 种 Prompt 模板（Minimal, Benchmark, Non-semantic, Order-variant）；最终导出为 `test_prompts.jsonl`。"

### 👤 姜 (P2 - API Architect)

**AI 助手指令：** "请帮我编写 `src/02_api_runner.py`。任务包括：对接 OpenRouter API，支持 `gpt-4o-mini`, `gemini-2.0-flash-001`, `claude-3.5-haiku` 和 `llama-3.1-8b`；设置 `temperature=0` 和 `max_tokens=50`；实现带指数退避的错误重试机制；读取 `test_prompts.jsonl` 并将模型响应保存至 `raw_responses.jsonl`。"

### 👤 孟 (P3 - Statistician)

**AI 助手指令：** "请帮我编写 `src/04_analysis.ipynb` 的统计核心。任务包括：实现一个 Bootstrap 函数，对准确率进行 $r=100$ 次重采样并计算 95% 置信区间；定义排名逆转率 (RRR) 的计算逻辑；使用模拟数据预先生成可视化图表框架（Boxplot 和 Heatmap）。"

### 👤 张 (P4 - Eval Scorer)

**AI 助手指令：** "请帮我编写 `src/03_scorer.py`。任务包括：设计鲁棒的正则表达式，从模型的原始输出中提取 A/B/C/D 选项；处理类似 'The correct answer is (A)' 的变体；将解析结果与 `gold_label` 对比，生成包含 0/1 得分的 `scored_results.csv`；记录无法解析的异常输出。"

---

## 🛠️ 关键决策记录 (Decision Log)

| 日期       | 决策内容                  | 理由                              | 负责人 |
| :--------- | :------------------------ | :-------------------------------- | :----- |
| 2026-03-20 | 确定使用 4 种 Prompt 模板 | 覆盖从极简到复杂指令的鲁棒性测试  | 全员   |
| 2026-03-20 | 固定样本量$n=300$       | 在统计效力与 API 预算之间取得平衡 | 全员   |

---

## ⚠️ 待处理风险 (Blockers & Risks)

- [ ] **OpenRouter 速率限制**：需要确认 haiku 模型的并发上限。
- [ ] **正则漏检**：Llama 模型可能输出非标准格式，需人工校验首批 15 题。

---



2026/03/23 PENG
Modified prompt templates so that they state clearer that the model should reply with only one letter