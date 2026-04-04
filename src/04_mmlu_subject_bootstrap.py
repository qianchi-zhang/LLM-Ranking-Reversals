from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from resampling_metrics import (
    INPUT_CSV,
    RESAMPLE_ITERATIONS,
    TEMPLATE_LABELS,
    TEMPLATE_ORDER,
    build_score_array,
    compute_subset_prompt_accuracy,
    create_accuracy_tables,
    create_resampling_tables,
    create_subset_accuracy_long,
    sample_half_subsets,
)


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "04_mmlu_subject_analysis"
PLOTS_DIR = BASE_DIR / "plots"
REPORTS_DIR = BASE_DIR / "reports"
SEED = 20260405
MMLU_SUBJECT_ORDER = [
    "formal_logic",
    "high_school_macroeconomics",
    "college_medicine",
    "high_school_physics",
    "philosophy",
    "international_law",
]
SUBJECT_SET_IDS = {
    subject: f"MMLU_S{index}"
    for index, subject in enumerate(MMLU_SUBJECT_ORDER, start=1)
}


def add_subject_metadata(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["subject_set_id"] = enriched["scope_value"].map(SUBJECT_SET_IDS)
    enriched["subject_name"] = enriched["scope_value"]
    enriched["scope_label"] = enriched["subject_set_id"] + " (" + enriched["subject_name"] + ")"
    return enriched


def ordered_subject_labels(df: pd.DataFrame) -> list[str]:
    scope_to_label = df[["scope_value", "scope_label"]].drop_duplicates().set_index("scope_value")["scope_label"]
    return [scope_to_label[subject] for subject in MMLU_SUBJECT_ORDER if subject in scope_to_label.index]


def plot_subject_accuracy(subject_overall: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    x_labels = ordered_subject_labels(subject_overall)
    model_labels = sorted(subject_overall["model_label"].unique())
    x = np.arange(len(x_labels))
    offsets = np.linspace(-0.3, 0.3, len(model_labels))
    width = 0.18

    fig, ax = plt.subplots(figsize=(16, 6))
    for idx, model_label in enumerate(model_labels):
        subset = (
            subject_overall.loc[subject_overall["model_label"] == model_label]
            .set_index("scope_label")
            .reindex(x_labels)
        )
        ax.bar(x + offsets[idx], subset["accuracy"].to_numpy(), width=width, label=model_label)

    ax.set_title("MMLU Subject-Level Prompt-Averaged Accuracy")
    ax.set_xlabel("Subject")
    ax.set_ylabel("Accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=4)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_accuracy.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_subject_prrr(subject_prrr: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    x_labels = ordered_subject_labels(subject_prrr)
    compared_labels = subject_prrr["compared_template_label"].drop_duplicates().tolist()
    pivot = (
        subject_prrr.pivot(
            index="scope_label",
            columns="compared_template_label",
            values="prrr",
        )
        .reindex(x_labels)
        .reindex(columns=compared_labels)
    )
    x = np.arange(len(x_labels))
    offsets = np.linspace(-0.25, 0.25, len(compared_labels))
    width = 0.22

    fig, ax = plt.subplots(figsize=(16, 6))
    for idx, compared_label in enumerate(compared_labels):
        ax.bar(x + offsets[idx], pivot[compared_label].to_numpy(), width=width, label=compared_label)

    ax.set_title("MMLU Subject-Level PRRR")
    ax.set_xlabel("Subject")
    ax.set_ylabel("PRRR")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_prrr.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_subject_srrr(subject_srrr: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    x_labels = ordered_subject_labels(subject_srrr)
    template_labels = [TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER]
    pivot = (
        subject_srrr.pivot(index="scope_label", columns="template_label", values="srrr")
        .reindex(x_labels)
        .reindex(columns=template_labels)
    )
    x = np.arange(len(x_labels))
    offsets = np.linspace(-0.3, 0.3, len(template_labels))
    width = 0.18

    fig, ax = plt.subplots(figsize=(16, 6))
    for idx, template_label in enumerate(template_labels):
        ax.bar(x + offsets[idx], pivot[template_label].to_numpy(), width=width, label=template_label)

    ax.set_title("MMLU Subject-Level SRRR")
    ax.set_xlabel("Subject")
    ax.set_ylabel("SRRR")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_srrr.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_report(
    subject_overall: pd.DataFrame,
    subject_prrr: pd.DataFrame,
    subject_srrr: pd.DataFrame,
) -> str:
    lines = [
        "# MMLU Subject Resampling Summary",
        "",
        "## Scope",
        "",
        "- Data source: `data/03_scored/scored_results.csv` restricted to the 300 MMLU items.",
        "- Subjects analyzed: the 6 fixed Phase 1 MMLU subjects, 50 items per subject.",
        f"- Resampling iterations per subject: {RESAMPLE_ITERATIONS}.",
        "- Each subject subset uses 25 items drawn without replacement from that subject's 50-item pool.",
        "",
        "## Key Findings",
        "",
    ]

    for subject in MMLU_SUBJECT_ORDER:
        overall_sub = subject_overall.loc[subject_overall["scope_value"] == subject].sort_values("rank")
        if overall_sub.empty:
            continue
        winner = overall_sub.iloc[0]
        top_prrr = (
            subject_prrr.loc[subject_prrr["scope_value"] == subject]
            .sort_values("prrr", ascending=False)
            .iloc[0]
        )
        top_srrr = (
            subject_srrr.loc[subject_srrr["scope_value"] == subject]
            .sort_values("srrr", ascending=False)
            .iloc[0]
        )
        lines.append(
            f"- {winner['scope_label']}: winner is {winner['model_label']} at {winner['accuracy']:.2%}; "
            f"max PRRR = {top_prrr['base_template_label']} vs {top_prrr['compared_template_label']} ({top_prrr['prrr']:.2%}); "
            f"max SRRR = {top_srrr['template_label']} ({top_srrr['srrr']:.2%})."
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_overall_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_prompt_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_prompt_ranking_reversal_rate.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_subset_ranking_reversal_rate.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_rank_probability.csv`",
            "- `data/04_mmlu_subject_analysis/mmlu_subject_subset_accuracy_long.csv`",
            "- `plots/mmlu_subject_accuracy.png`",
            "- `plots/mmlu_subject_prrr.png`",
            "- `plots/mmlu_subject_srrr.png`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    mmlu_df = df.loc[df["dataset"] == "mmlu"].copy()
    rng = np.random.default_rng(SEED)

    prompt_tables = []
    overall_tables = []
    prrr_tables = []
    srrr_tables = []
    rank_prob_tables = []
    subset_accuracy_tables = []

    for subject in MMLU_SUBJECT_ORDER:
        subject_df = mmlu_df.loc[mmlu_df["subject"] == subject].copy()
        if subject_df.empty:
            continue

        score_array, item_order, model_order = build_score_array(
            subject_df,
            f"MMLU subject {subject}",
        )
        subset_indices = sample_half_subsets(len(item_order), rng)
        subset_prompt_acc = compute_subset_prompt_accuracy(score_array, subset_indices)
        full_prompt_acc = score_array.mean(axis=0)

        prompt_df, overall_df = create_accuracy_tables(
            "mmlu_subject",
            subject,
            model_order,
            score_array,
        )
        prrr_df, srrr_df, rank_prob_df = create_resampling_tables(
            "mmlu_subject",
            subject,
            model_order,
            full_prompt_acc,
            subset_prompt_acc,
        )
        subset_accuracy_df = create_subset_accuracy_long(
            "mmlu_subject",
            subject,
            model_order,
            subset_prompt_acc,
        )

        prompt_tables.append(add_subject_metadata(prompt_df))
        overall_tables.append(add_subject_metadata(overall_df))
        prrr_tables.append(add_subject_metadata(prrr_df))
        srrr_tables.append(add_subject_metadata(srrr_df))
        rank_prob_tables.append(add_subject_metadata(rank_prob_df))
        subset_accuracy_tables.append(add_subject_metadata(subset_accuracy_df))

        print(
            f"Analyzed MMLU subject {subject}: {len(item_order)} items, subset size {len(item_order) // 2}."
        )

    subject_prompt = pd.concat(prompt_tables, ignore_index=True)
    subject_overall = pd.concat(overall_tables, ignore_index=True)
    subject_prrr = pd.concat(prrr_tables, ignore_index=True)
    subject_srrr = pd.concat(srrr_tables, ignore_index=True)
    subject_rank_prob = pd.concat(rank_prob_tables, ignore_index=True)
    subject_subset_accuracy = pd.concat(subset_accuracy_tables, ignore_index=True)

    subject_overall.to_csv(OUTPUT_DIR / "mmlu_subject_overall_accuracy.csv", index=False)
    subject_prompt.to_csv(OUTPUT_DIR / "mmlu_subject_prompt_accuracy.csv", index=False)
    subject_prrr.to_csv(
        OUTPUT_DIR / "mmlu_subject_prompt_ranking_reversal_rate.csv",
        index=False,
    )
    subject_srrr.to_csv(
        OUTPUT_DIR / "mmlu_subject_subset_ranking_reversal_rate.csv",
        index=False,
    )
    subject_rank_prob.to_csv(OUTPUT_DIR / "mmlu_subject_rank_probability.csv", index=False)
    subject_subset_accuracy.to_csv(
        OUTPUT_DIR / "mmlu_subject_subset_accuracy_long.csv",
        index=False,
    )

    plot_subject_accuracy(subject_overall)
    plot_subject_prrr(subject_prrr)
    plot_subject_srrr(subject_srrr)

    report = build_report(subject_overall, subject_prrr, subject_srrr)
    (REPORTS_DIR / "mmlu_subject_bootstrap_summary.md").write_text(report, encoding="utf-8")

    print(f"Saved MMLU subject analysis to: {OUTPUT_DIR}")
    print(f"Saved plots to: {PLOTS_DIR}")
    print(f"Saved report to: {REPORTS_DIR / 'mmlu_subject_bootstrap_summary.md'}")


if __name__ == "__main__":
    main()
