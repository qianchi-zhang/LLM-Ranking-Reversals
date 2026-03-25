from __future__ import annotations

from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "03_scored" / "scored_results.csv"
OUTPUT_DIR = BASE_DIR / "data" / "04_mmlu_subject_analysis"
PLOTS_DIR = BASE_DIR / "plots"
REPORTS_DIR = BASE_DIR / "reports"

BOOTSTRAP_ITERATIONS = 2000
SEED = 20260325
BASE_TEMPLATE = "minimal_instruction"
TEMPLATE_ORDER = [
    "minimal_instruction",
    "benchmark_style",
    "natural_style",
    "order_phrasing_variation",
]
TEMPLATE_LABELS = {
    "minimal_instruction": "Minimal",
    "benchmark_style": "Benchmark",
    "natural_style": "Natural",
    "order_phrasing_variation": "Order/Phrasing",
}
MODEL_LABELS = {
    "openai/gpt-4o-mini": "GPT-4o-mini",
    "google/gemini-2.0-flash-001": "Gemini-2.0-flash",
    "meta-llama/llama-3.1-8b-instruct": "Llama-3.1-8B",
    "qwen/qwen-2.5-7b-instruct": "Qwen-2.5-7B",
}


def short_model_name(model_id: str) -> str:
    return MODEL_LABELS.get(model_id, model_id.split("/")[-1])


def percentile_ci(values: np.ndarray, lower: float = 2.5, upper: float = 97.5) -> tuple[float, float]:
    return float(np.percentile(values, lower)), float(np.percentile(values, upper))


def bootstrap_p_value(diff: np.ndarray) -> float:
    p_lower = float(np.mean(diff <= 0))
    p_upper = float(np.mean(diff >= 0))
    return min(1.0, 2 * min(p_lower, p_upper))


def make_order_matrix(scores: np.ndarray) -> np.ndarray:
    num_models = scores.shape[1]
    tie_break = np.linspace(0, 1e-10, num_models, endpoint=False)
    adjusted = scores + tie_break
    return np.argsort(-adjusted, axis=1, kind="mergesort")


def prepare_mmlu_panel(df: pd.DataFrame, subject: str | None = None):
    subset = df.loc[df["dataset"] == "mmlu"].copy()
    if subject is not None:
        subset = subset.loc[subset["subject"] == subject].copy()

    subset["template_name"] = pd.Categorical(subset["template_name"], categories=TEMPLATE_ORDER, ordered=True)
    model_order = sorted(subset["model_id"].unique(), key=short_model_name)
    item_meta = subset[["item_id", "subject"]].drop_duplicates().sort_values(["subject", "item_id"]).reset_index(drop=True)
    item_order = item_meta["item_id"].tolist()

    pivot = subset.pivot_table(
        index="item_id",
        columns=["model_id", "template_name"],
        values="score",
        aggfunc="first",
    ).reindex(item_order)

    column_index = pd.MultiIndex.from_product([model_order, TEMPLATE_ORDER], names=["model_id", "template_name"])
    pivot = pivot.reindex(columns=column_index)

    if pivot.isna().any().any():
        missing = int(pivot.isna().sum().sum())
        raise ValueError(f"MMLU panel has {missing} missing score entries.")

    score_array = pivot.to_numpy(dtype=float).reshape(len(item_order), len(model_order), len(TEMPLATE_ORDER))
    return score_array, item_meta, model_order


def bootstrap_indices_simple(n_items: int, rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, n_items, size=(BOOTSTRAP_ITERATIONS, n_items))


def bootstrap_indices_stratified(group_indices: list[np.ndarray], rng: np.random.Generator) -> np.ndarray:
    sampled_groups = []
    for indices in group_indices:
        sampled_groups.append(rng.choice(indices, size=(BOOTSTRAP_ITERATIONS, len(indices)), replace=True))
    return np.concatenate(sampled_groups, axis=1)


def summarize_panel(score_array: np.ndarray, bootstrap_idx: np.ndarray, model_order: list[str], scope: str, scope_value: str):
    sampled = score_array[bootstrap_idx]
    boot_prompt_acc = sampled.mean(axis=1)
    boot_overall_acc = sampled.mean(axis=(1, 3))
    point_prompt = score_array.mean(axis=0)
    overall_point = score_array.mean(axis=(0, 2))

    prompt_rows = []
    for model_idx, model_id in enumerate(model_order):
        for template_idx, template_name in enumerate(TEMPLATE_ORDER):
            ci_low, ci_high = percentile_ci(boot_prompt_acc[:, model_idx, template_idx])
            prompt_rows.append(
                {
                    "scope": scope,
                    "scope_value": scope_value,
                    "model_id": model_id,
                    "model_label": short_model_name(model_id),
                    "template_name": template_name,
                    "template_label": TEMPLATE_LABELS[template_name],
                    "accuracy": float(point_prompt[model_idx, template_idx]),
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                }
            )

    ranking = sorted(range(len(model_order)), key=lambda idx: (-overall_point[idx], short_model_name(model_order[idx])))
    rank_lookup = {model_order[idx]: rank + 1 for rank, idx in enumerate(ranking)}

    overall_rows = []
    for model_idx, model_id in enumerate(model_order):
        ci_low, ci_high = percentile_ci(boot_overall_acc[:, model_idx])
        overall_rows.append(
            {
                "scope": scope,
                "scope_value": scope_value,
                "model_id": model_id,
                "model_label": short_model_name(model_id),
                "accuracy": float(overall_point[model_idx]),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "rank": rank_lookup[model_id],
            }
        )

    pairwise_rows = []
    for left_idx, right_idx in combinations(range(len(model_order)), 2):
        left_model = model_order[left_idx]
        right_model = model_order[right_idx]
        diff = boot_overall_acc[:, left_idx] - boot_overall_acc[:, right_idx]
        ci_low, ci_high = percentile_ci(diff)
        pairwise_rows.append(
            {
                "scope": scope,
                "scope_value": scope_value,
                "left_model_id": left_model,
                "left_model_label": short_model_name(left_model),
                "right_model_id": right_model,
                "right_model_label": short_model_name(right_model),
                "point_diff": float(overall_point[left_idx] - overall_point[right_idx]),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "p_value": bootstrap_p_value(diff),
                "significant_95": not (ci_low <= 0 <= ci_high),
            }
        )

    order_matrices = {
        template: make_order_matrix(boot_prompt_acc[:, :, template_idx])
        for template_idx, template in enumerate(TEMPLATE_ORDER)
    }
    base_orders = order_matrices[BASE_TEMPLATE]
    rrr_rows = []
    for template_name, orders in order_matrices.items():
        if template_name == BASE_TEMPLATE:
            continue
        rrr_rows.append(
            {
                "scope": scope,
                "scope_value": scope_value,
                "template_name": template_name,
                "template_label": TEMPLATE_LABELS[template_name],
                "rrr": float(np.any(orders != base_orders, axis=1).mean()),
            }
        )

    return (
        pd.DataFrame(prompt_rows),
        pd.DataFrame(overall_rows),
        pd.DataFrame(pairwise_rows),
        pd.DataFrame(rrr_rows),
    )


def plot_subject_accuracy(subject_overall: pd.DataFrame):
    plt.style.use("ggplot")
    subjects = subject_overall["scope_value"].unique().tolist()
    model_labels = sorted(subject_overall["model_label"].unique())
    x = np.arange(len(subjects))
    offsets = np.linspace(-0.3, 0.3, len(model_labels))
    width = 0.18

    fig, ax = plt.subplots(figsize=(14, 6))
    for idx, model_label in enumerate(model_labels):
        subset = subject_overall.loc[subject_overall["model_label"] == model_label].set_index("scope_value").reindex(subjects)
        ax.bar(x + offsets[idx], subset["accuracy"].to_numpy(), width=width, label=model_label)

    ax.set_title("MMLU Subject-Level Accuracy by Model")
    ax.set_xlabel("Subject")
    ax.set_ylabel("Prompt-Averaged Accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(subjects, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=4)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_accuracy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_subject_rrr(subject_rrr: pd.DataFrame):
    plt.style.use("ggplot")
    subjects = subject_rrr["scope_value"].unique().tolist()
    template_labels = [TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER if name != BASE_TEMPLATE]
    pivot = subject_rrr.pivot(index="scope_value", columns="template_label", values="rrr").reindex(subjects).reindex(columns=template_labels)
    x = np.arange(len(subjects))
    offsets = np.linspace(-0.25, 0.25, len(template_labels))
    width = 0.22

    fig, ax = plt.subplots(figsize=(14, 6))
    for idx, template_label in enumerate(template_labels):
        ax.bar(x + offsets[idx], pivot[template_label].to_numpy(), width=width, label=template_label)

    ax.set_title("MMLU Subject-Level Ranking Reversal Rate")
    ax.set_xlabel("Subject")
    ax.set_ylabel("RRR")
    ax.set_xticks(x)
    ax.set_xticklabels(subjects, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_rrr.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_report(scheme_overall: pd.DataFrame, scheme_rrr: pd.DataFrame, subject_overall: pd.DataFrame, subject_rrr: pd.DataFrame) -> str:
    lines = [
        "# MMLU Subject Bootstrap Summary",
        "",
        "## Current Bootstrap Design",
        "",
        "- The original `04_analysis.py` uses plain item-level bootstrap within each dataset.",
        "- For MMLU, that means sampling with replacement from all 300 items pooled together.",
        "- It does not preserve the 6-subject composition during each bootstrap iteration.",
        "",
        "## New Subject-Aware Designs",
        "",
        "- `overall_pooled`: resample from all 300 MMLU items directly.",
        "- `overall_stratified`: resample within each of the 6 subjects, keeping 50 items per subject in every iteration.",
        "- `subject_only`: run bootstrap separately on each subject's 50 items.",
        "",
        "## Comparison of Pooled vs Stratified Full-MMLU Bootstrap",
        "",
    ]

    for scope_value in ["overall_pooled", "overall_stratified"]:
        subset = scheme_overall.loc[scheme_overall["scope_value"] == scope_value].sort_values("rank")
        summary = ", ".join(f"{row.model_label}={row.accuracy:.2%}(rank {int(row.rank)})" for row in subset.itertuples())
        lines.append(f"- {scope_value}: {summary}")

    lines.extend(["", "## Subject-Level Highlights", ""])

    for subject in subject_overall["scope_value"].unique():
        overall_sub = subject_overall.loc[subject_overall["scope_value"] == subject].sort_values("rank")
        winner = overall_sub.iloc[0]
        lines.append(
            f"- {subject}: winner is {winner['model_label']} at {winner['accuracy']:.2%}; ranking order = "
            + " > ".join(overall_sub["model_label"].tolist())
        )

    avg_rrr = subject_rrr.groupby("scope_value", as_index=False)["rrr"].mean().sort_values("rrr", ascending=False)
    if not avg_rrr.empty:
        lines.extend(["", "## Most Unstable Subjects", ""])
        for row in avg_rrr.itertuples(index=False):
            lines.append(f"- {row.scope_value}: mean RRR across non-minimal prompts = {row.rrr:.2%}")

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `data/04_mmlu_subject_analysis/mmlu_scheme_overall_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_scheme_rrr.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_overall_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_prompt_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_rrr.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_pairwise_significance.csv`",
            "- `plots/mmlu_subject_accuracy.png`",
            "- `plots/mmlu_subject_rrr.png`",
        ]
    )

    return "\n".join(lines) + "\n"


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    rng = np.random.default_rng(SEED)

    full_array, full_meta, model_order = prepare_mmlu_panel(df)
    pooled_idx = bootstrap_indices_simple(len(full_meta), rng)
    subject_groups = [group.index.to_numpy() for _, group in full_meta.groupby("subject", sort=True)]
    stratified_idx = bootstrap_indices_stratified(subject_groups, rng)

    pooled_prompt, pooled_overall, pooled_pairs, pooled_rrr = summarize_panel(full_array, pooled_idx, model_order, "scheme", "overall_pooled")
    strat_prompt, strat_overall, strat_pairs, strat_rrr = summarize_panel(full_array, stratified_idx, model_order, "scheme", "overall_stratified")

    scheme_overall = pd.concat([pooled_overall, strat_overall], ignore_index=True)
    scheme_prompt = pd.concat([pooled_prompt, strat_prompt], ignore_index=True)
    scheme_pairs = pd.concat([pooled_pairs, strat_pairs], ignore_index=True)
    scheme_rrr = pd.concat([pooled_rrr, strat_rrr], ignore_index=True)

    subject_prompt_tables = []
    subject_overall_tables = []
    subject_pair_tables = []
    subject_rrr_tables = []

    for subject in full_meta["subject"].unique():
        sub_array, _, sub_model_order = prepare_mmlu_panel(df, subject=subject)
        sub_idx = bootstrap_indices_simple(sub_array.shape[0], rng)
        prompt_df, overall_df, pair_df, rrr_df = summarize_panel(sub_array, sub_idx, sub_model_order, "subject", subject)
        subject_prompt_tables.append(prompt_df)
        subject_overall_tables.append(overall_df)
        subject_pair_tables.append(pair_df)
        subject_rrr_tables.append(rrr_df)
        print(f"Analyzed MMLU subject: {subject}")

    subject_prompt = pd.concat(subject_prompt_tables, ignore_index=True)
    subject_overall = pd.concat(subject_overall_tables, ignore_index=True)
    subject_pairs = pd.concat(subject_pair_tables, ignore_index=True)
    subject_rrr = pd.concat(subject_rrr_tables, ignore_index=True)

    scheme_overall.to_csv(OUTPUT_DIR / "mmlu_scheme_overall_accuracy.csv", index=False)
    scheme_prompt.to_csv(OUTPUT_DIR / "mmlu_scheme_prompt_accuracy.csv", index=False)
    scheme_pairs.to_csv(OUTPUT_DIR / "mmlu_scheme_pairwise_significance.csv", index=False)
    scheme_rrr.to_csv(OUTPUT_DIR / "mmlu_scheme_rrr.csv", index=False)

    subject_overall.to_csv(OUTPUT_DIR / "mmlu_subject_overall_accuracy.csv", index=False)
    subject_prompt.to_csv(OUTPUT_DIR / "mmlu_subject_prompt_accuracy.csv", index=False)
    subject_pairs.to_csv(OUTPUT_DIR / "mmlu_subject_pairwise_significance.csv", index=False)
    subject_rrr.to_csv(OUTPUT_DIR / "mmlu_subject_rrr.csv", index=False)

    plot_subject_accuracy(subject_overall)
    plot_subject_rrr(subject_rrr)

    report = build_report(scheme_overall, scheme_rrr, subject_overall, subject_rrr)
    (REPORTS_DIR / "mmlu_subject_bootstrap_summary.md").write_text(report, encoding="utf-8")

    print(f"Saved MMLU subject analysis to: {OUTPUT_DIR}")
    print(f"Saved plots to: {PLOTS_DIR}")
    print(f"Saved report to: {REPORTS_DIR / 'mmlu_subject_bootstrap_summary.md'}")


if __name__ == "__main__":
    main()
