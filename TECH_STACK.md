# 🛠️ Tech Stack & Environment Guide

This document outlines the standard technology stack, libraries, and environment configurations for the **LLM Ranking Reversals** project (Group 14). All team members must adhere to these standards to ensure reproducibility and prevent integration conflicts.

---

## 1. Core Environment

* **Language**: Python 3.10 or 3.11 (Recommended for `aiohttp` and modern typing support).
* **Environment Management**: Use `conda` or `venv` to create an isolated virtual environment.
* **Data Exchange Formats**:
  * **API I/O**: `JSONL` (`.jsonl`) - Used for prompts and raw model responses to allow append-only writing and prevent data loss during API interruptions.
  * **Analysis I/O**: `CSV` (`.csv`) - Used for the final scored results, easily loadable into Pandas.

---

## 2. Module-Specific Stack & Ownership

### Module 1: Data & Prompt Engineering (Owner: Peng)

Responsible for fetching datasets and generating prompt perturbations.

* **`datasets`** (HuggingFace): For downloading MMLU, ARC-Challenge, and HellaSwag seamlessly.
* **`pandas`**: For data manipulation, stratified sampling, and shuffling.
* **`json`** (Built-in): For structured I/O of `.jsonl` files.

### Module 2: API Orchestration (Owner: Jiang)

Responsible for concurrent LLM inference via OpenRouter.

* **`aiohttp` & `asyncio`**: For high-throughput, asynchronous API requests (crucial for handling 14,400+ calls efficiently).
* **`tenacity`**: For implementing exponential backoff and retry logic to handle `429 Rate Limit` and `502 Bad Gateway` errors.
* **`python-dotenv`**: For securely loading `OPENROUTER_API_KEY` from a local `.env` file without hardcoding secrets.

### Module 3: Parsing & Scoring (Owner: Meng)

Responsible for extracting final answers from verbose LLM outputs.

* **`re`** (Built-in): For writing regular expressions (Regex) to capture "A/B/C/D" from diverse response formats.
* **`pandas`**: For merging extracted answers with gold labels to generate binary scores (1/0).

### Module 4: Statistical Analysis (Owner: Zhang)

Responsible for computing confidence intervals, ranking reversal rates, and visualizations.

* **`numpy`**: For efficient Bootstrap resampling operations.
* **`scipy.stats`**: For computing standard errors and 95% Confidence Intervals (CI).
* **`matplotlib` & `seaborn`**: For generating publication-ready visualizations (e.g., Boxplots of accuracy variance, Rank Probability Heatmaps).

---

## 3. Collaboration Infrastructure

* **Version Control**: Git & GitHub (Private Repository).
* **Documentation**: Overleaf (LaTeX) for the final report.
* **IDE Recommendations**:
  * *Peng, Jiang, Zhang*: VS Code or PyCharm (Best for `.py` scripting and debugging).
  * *Meng*: Jupyter Notebook / JupyterLab (Best for `.ipynb` statistical exploration and plotting).

---

## 4. Quick Setup (`requirements.txt`)

Save the following content as `requirements.txt` in the root directory:

```text
# Data Processing
datasets>=2.16.0
pandas>=2.0.0
numpy>=1.24.0

# API & Async Networking
aiohttp>=3.9.0
tenacity>=8.2.0
python-dotenv>=1.0.0

# Statistical Analysis & Visualization
scipy>=1.10.0
matplotlib>=3.7.0
seaborn>=0.13.0

# Notebook support
jupyter>=1.0.0
```
