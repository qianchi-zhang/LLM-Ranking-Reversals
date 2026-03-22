# 🚀 ST5230 Project: LLM Ranking Reversals

**Group 14 Team Members:** ZHANG QIANCHI, PENG YANGYUNZHI, JIANG YIFAN, MENG XIANGCHEN

## About The Project

This repository contains the codebase for our ST5230 (Applied Natural Language Processing) course project. We study the statistical reliability of Large Language Model (LLM) benchmarks, focusing on how non-semantic prompt perturbations and sampling noise can induce ranking reversals among state-of-the-art models.

## Project Goals

- Measure ranking stability under prompt variations and resampling noise.
- Quantify ranking reversal rates across common benchmarks (MMLU, ARC-Challenge, HellaSwag).
- Produce reproducible analysis with transparent data, prompts, and code.

## Models Evaluated

All inference is conducted via OpenRouter API with fixed decoding parameters (`temperature=0`, `top_p=1`):
- `openai/gpt-4o-mini`
- `anthropic/claude-3.5-haiku`
- `google/gemini-2.0-flash-001`
- `meta-llama/llama-3.1-8b-instruct`

---

## 📂 Repository Structure

Our codebase follows a strict 4-phase pipeline architecture:

```text
LLM-Ranking-Reversals/
├── docs/                            # Project documentation & proposals
├── src/                             # Core execution pipeline
│   ├── 01_data_prep.py              # Phase 1: Sample datasets & apply 4 prompt templates
│   ├── 02_api_runner.py             # Phase 2: Async LLM inference via OpenRouter
│   ├── 03_scorer.py                 # Phase 3: Regex-based answer extraction & scoring
│   ├── 04_analysis.ipynb            # Phase 4: Bootstrap resampling & RRR calculation
│   └── utils/                       # Shared utilities (Regex patterns, Prompts)
├── data/                            # Local data storage (Ignored in Git)
│   ├── 01_prompts/                  # Output of Phase 1 (master_prompts.jsonl)
│   ├── 02_raw_responses/            # Output of Phase 2 (raw_responses.jsonl)
│   └── 03_scored/                   # Output of Phase 3 (scored_results.csv)
└── plots/                           # Generated visualizations for the final report
```

---

## ⚙️ Environment Setup

To ensure reproducibility and avoid dependency conflicts, all team members must use **Python 3.11** and the standard project environment named `llm-ranking-env`.

### Prerequisites
1. Ensure you have Miniconda or Python 3.11 installed.
2. Clone this repository to your local machine.

### Using Conda (Recommended)
Open your terminal and run the following commands:

```bash
# 1. Create a Python 3.11 environment named llm-ranking-env
conda create -n llm-ranking-env python=3.11 -y

# 2. Activate the environment
conda activate llm-ranking-env

# 3. Install required packages
pip install -r requirements.txt

# 4. Register the environment to Jupyter (for Phase 4 Analysis)
python -m ipykernel install --user --name=llm-ranking-env --display-name "Python 3.11 (llm-ranking-env)"
```

### 🔑 Setting up API Keys
This project uses OpenRouter for LLM inference. **NEVER commit your API key to GitHub.**

1. In the root directory, create a file named `.env`.
2. Add your API key to the file:
   ```text
   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🏃 Getting Started (Execution Pipeline)

To reproduce our experiments, execute the scripts in the following order:

1. **Phase 1 (Data Prep):** `python src/01_data_prep.py`
   *Samples balanced subsets and generates 4 prompt variants per question. Outputs `master_prompts.jsonl`.*
2. **Phase 2 (Inference):** `python src/02_api_runner.py`
   *Runs async API calls with exponential backoff. Outputs `raw_responses.jsonl`.*
3. **Phase 3 (Scoring):** `python src/03_scorer.py`
   *Parses LLM outputs using Regex against gold labels. Outputs `scored_results.csv`.*
4. **Phase 4 (Analysis):** Open `src/04_analysis.ipynb` in Jupyter Notebook.
   *Executes Bootstrap resampling to estimate confidence intervals and generates plots.*

---

## 📚 Documentation & References

- [Project Execution Plan](docs/EXECUTION_PLAN.md): Detailed experimental protocol and methodology.
- [Project Log](PROJECT_LOG.md): Team task assignments, progress tracking, and decision logs.
- [Tech Stack Guide](TECH_STACK.md): Detailed library dependencies and coding standards.