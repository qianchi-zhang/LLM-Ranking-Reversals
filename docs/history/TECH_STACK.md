# 技术栈记录（归档整理版）

## 1. 文档性质

本文件用于记录项目历史上采用过、讨论过或计划过的技术栈，并说明当前仓库中真正落地的版本。

## 2. 当前实际技术栈

### 运行环境

- Python 3.11
- `pip` + `requirements.txt`
- 推荐使用 `conda` 或 `venv`

### 数据与实验脚本

- `datasets`
- `pandas`
- `numpy`
- `matplotlib`
- `scipy`

### API 调用

- `requests`
- `python-dotenv`
- `tenacity`
- `tqdm`

### 数据交换格式

- `JSONL`：prompt 请求与原始响应
- `CSV`：评分与分析结果

## 3. 历史上讨论过但未完全保留的技术选项

早期计划中曾讨论过：

- 使用 `aiohttp` / `asyncio` 做高并发 API 调用；
- 使用 Claude 作为正式比较模型之一；
- 以 notebook 为主要分析与运行入口。

这些方案并非全部成为当前最终实现。当前实际仓库中：

- Phase 2 标准脚本使用 `requests`，而不是异步并发版本；
- 最终进入分析的数据不包含 Claude，而包含 Qwen；
- notebook 保留为历史来源，标准复现入口收敛为脚本与 `run_pipeline.py`。

## 4. 当前推荐做法

- 统一通过 `requirements.txt` 安装依赖；
- 统一通过 `run_pipeline.py` 或 `src/01~04_*.py` 运行；
- 将新增技术说明补充到 `docs/`，而不是继续把标准说明写在历史文档中。
