# Legacy Scripts

`src/legacy/` 用于存放历史试验脚本、原型脚本或已经退出主流水线的旧实现。

这些文件不属于当前标准复现入口。当前推荐入口仍然是：

- `python run_pipeline.py`
- `python src/01_data_prep.py`
- `python src/02_api_runner.py`
- `python src/03_scorer.py`
- `python src/04_analysis.py`
- `python src/04_mmlu_subject_bootstrap.py`

如果 `src/legacy/` 中的脚本与当前主流水线冲突，以主流水线为准。
