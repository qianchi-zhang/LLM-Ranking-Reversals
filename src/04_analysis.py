from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from resampling_metrics import (
    BASE_TEMPLATE,
    DATASET_LABELS,
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
ANALYSIS_DIR = BASE_DIR / "data" / "04_analysis"
PLOTS_DIR = BASE_DIR / "plots"
REPORTS_DIR = BASE_DIR / "reports"
SEED = 20260404


def plot_accuracy_boxplots(subset_accuracy_long: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    datasets = sorted(subset_accuracy_long["scope_value"].unique())
    model_labels = sorted(subset_accuracy_long["model_label"].unique())
    fig, axes = plt.subplots(1, len(datasets), figsize=(18, 6), sharey=True)
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])

    color_map = plt.get_cmap("tab10", len(model_labels))
    offsets = np.linspace(-0.27, 0.27, len(model_labels))
    width = 0.16

    for axis, dataset in zip(axes, datasets):
        subset = subset_accuracy_long.loc[subset_accuracy_long["scope_value"] == dataset]
        positions = np.arange(len(TEMPLATE_ORDER))
        for model_idx, model_label in enumerate(model_labels):
            series_list = []
            for template_name in TEMPLATE_ORDER:
                values = subset.loc[
                    (subset["model_label"] == model_label)
                    & (subset["template_name"] == template_name),
                    "accuracy_pct",
                ].to_numpy()
                series_list.append(values)

            axis.boxplot(
                series_list,
                positions=positions + offsets[model_idx],
                widths=width,
                patch_artist=True,
                showfliers=False,
                boxprops={"facecolor": color_map(model_idx), "alpha": 0.65},
                medianprops={"color": "black", "linewidth": 1.0},
                whiskerprops={"linewidth": 1.0},
                capprops={"linewidth": 1.0},
            )

        axis.set_title(DATASET_LABELS.get(dataset, dataset))
        axis.set_xlabel("Template")
        axis.set_ylabel("Subset Accuracy (%)")
        axis.set_xticks(positions)
        axis.set_xticklabels([TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER], rotation=20)

    handles = [
        plt.Line2D([0], [0], color=color_map(idx), lw=8, alpha=0.8)
        for idx in range(len(model_labels))
    ]
    fig.legend(handles, model_labels, loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(PLOTS_DIR / "accuracy_boxplots.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_prrr(prrr_df: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, 6))
    dataset_labels = [DATASET_LABELS[key] for key in sorted(prrr_df["scope_value"].unique())]
    compared_labels = [
        TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER if name != BASE_TEMPLATE
    ]
    pivot = (
        prrr_df.pivot(
            index="scope_label",
            columns="compared_template_label",
            values="prrr",
        )
        .reindex(dataset_labels)
        .reindex(columns=compared_labels)
    )
    x = np.arange(len(dataset_labels))
    offsets = np.linspace(-0.25, 0.25, len(compared_labels))
    bar_width = 0.22

    for idx, compared_label in enumerate(compared_labels):
        ax.bar(
            x + offsets[idx],
            pivot[compared_label].to_numpy(),
            width=bar_width,
            label=f"{TEMPLATE_LABELS[BASE_TEMPLATE]} vs {compared_label}",
        )

    ax.set_xlabel("Dataset")
    ax.set_ylabel("PRRR")
    ax.set_ylim(0, 1)
    ax.set_xticks(x)
    ax.set_xticklabels(dataset_labels)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "prompt_ranking_reversal_rate.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_srrr(srrr_df: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, 6))
    dataset_labels = [DATASET_LABELS[key] for key in sorted(srrr_df["scope_value"].unique())]
    template_labels = [TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER]
    pivot = (
        srrr_df.pivot(index="scope_label", columns="template_label", values="srrr")
        .reindex(dataset_labels)
        .reindex(columns=template_labels)
    )
    x = np.arange(len(dataset_labels))
    offsets = np.linspace(-0.3, 0.3, len(template_labels))
    bar_width = 0.18

    for idx, template_label in enumerate(template_labels):
        ax.bar(
            x + offsets[idx],
            pivot[template_label].to_numpy(),
            width=bar_width,
            label=template_label,
        )

    ax.set_xlabel("Dataset")
    ax.set_ylabel("SRRR")
    ax.set_ylim(0, 1)
    ax.set_xticks(x)
    ax.set_xticklabels(dataset_labels)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "subset_ranking_reversal_rate.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_rank_heatmaps(rank_probs: pd.DataFrame) -> None:
    plt.style.use("default")
    for dataset in sorted(rank_probs["scope_value"].unique()):
        subset = rank_probs.loc[rank_probs["scope_value"] == dataset]
        fig, axes = plt.subplots(2, 2, figsize=(12, 10), constrained_layout=True)
        axes = axes.flatten()
        image = None

        for axis, template_name in zip(axes, TEMPLATE_ORDER):
            template_subset = subset.loc[subset["template_name"] == template_name]
            pivot = (
                template_subset.pivot(
                    index="model_label",
                    columns="rank_position",
                    values="probability",
                )
                .reindex(sorted(template_subset["model_label"].unique()))
            )
            image = axis.imshow(
                pivot.to_numpy(),
                cmap="YlGnBu",
                vmin=0,
                vmax=1,
                aspect="auto",
            )
            axis.set_xticks(np.arange(pivot.shape[1]))
            axis.set_xticklabels(pivot.columns.tolist())
            axis.set_yticks(np.arange(pivot.shape[0]))
            axis.set_yticklabels(pivot.index.tolist())
            axis.set_title(TEMPLATE_LABELS[template_name])
            axis.set_xlabel("Rank Position")
            axis.set_ylabel("Model")
            for row_idx in range(pivot.shape[0]):
                for col_idx in range(pivot.shape[1]):
                    axis.text(
                        col_idx,
                        row_idx,
                        f"{pivot.iat[row_idx, col_idx]:.2f}",
                        ha="center",
                        va="center",
                        color="black",
                        fontsize=9,
                    )

        fig.suptitle(
            f"Subset Rank Probability - {DATASET_LABELS.get(dataset, dataset)}",
            y=0.98,
        )
        if image is not None:
            fig.colorbar(image, ax=axes, shrink=0.85, location="right")
        fig.savefig(
            PLOTS_DIR / f"{dataset}_rank_probability_heatmaps.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)


def build_markdown_report(
    overall_acc_df: pd.DataFrame,
    prrr_df: pd.DataFrame,
    srrr_df: pd.DataFrame,
    scored_df: pd.DataFrame,
) -> str:
    lines = [
        "# Dataset-Level Resampling Summary",
        "",
        "## Scope",
        "",
        "- Data source: `data/03_scored/scored_results.csv`.",
        "- No new API requests are made in Phase 4. All statistics reuse the fixed 14,400 scored responses from Phase 2 and Phase 3.",
        f"- Resampling iterations per scope: {RESAMPLE_ITERATIONS}.",
        "- Each resampled subset uses `n/2` items drawn without replacement from the current scope.",
        f"- PRRR compares `{BASE_TEMPLATE}` against each non-baseline template on the same half-sized subsets.",
        "- SRRR compares each template's full-set ranking against the ranking on resampled half-sized subsets.",
        "",
        "## Key Findings",
        "",
    ]

    parse_failures = int((~scored_df["is_parsed"]).sum())
    lines.append(
        f"- Parse failures remained low: {parse_failures} / {len(scored_df)} rows ({parse_failures / len(scored_df):.2%})."
    )

    for dataset in sorted(overall_acc_df["scope_value"].unique()):
        dataset_overall = overall_acc_df.loc[
            overall_acc_df["scope_value"] == dataset
        ].sort_values("rank")
        winner = dataset_overall.iloc[0]
        lines.append(
            f"- {winner['scope_label']}: prompt-averaged winner is {winner['model_label']} at {winner['accuracy']:.2%}."
        )

        dataset_prrr = prrr_df.loc[prrr_df["scope_value"] == dataset].sort_values(
            "prrr", ascending=False
        )
        top_prrr = dataset_prrr.iloc[0]
        lines.append(
            f"- {winner['scope_label']}: highest PRRR is {top_prrr['base_template_label']} vs {top_prrr['compared_template_label']} = {top_prrr['prrr']:.2%}."
        )

        dataset_srrr = srrr_df.loc[srrr_df["scope_value"] == dataset].sort_values(
            "srrr", ascending=False
        )
        top_srrr = dataset_srrr.iloc[0]
        lines.append(
            f"- {winner['scope_label']}: highest SRRR occurs under {top_srrr['template_label']} = {top_srrr['srrr']:.2%}."
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "- `data/04_analysis/accuracy_by_dataset_model.csv`",
            "- `data/04_analysis/accuracy_by_dataset_model_prompt.csv`",
            "- `data/04_analysis/prompt_ranking_reversal_rate.csv`",
            "- `data/04_analysis/subset_ranking_reversal_rate.csv`",
            "- `data/04_analysis/rank_probability.csv`",
            "- `data/04_analysis/subset_accuracy_long.csv`",
            "- `plots/accuracy_boxplots.png`",
            "- `plots/prompt_ranking_reversal_rate.png`",
            "- `plots/subset_ranking_reversal_rate.png`",
            "- `plots/*_rank_probability_heatmaps.png`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    scored_df = pd.read_csv(INPUT_CSV)

    required_columns = {"item_id", "dataset", "template_name", "model_id", "score", "is_parsed"}
    missing_columns = required_columns - set(scored_df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    rng = np.random.default_rng(SEED)

    prompt_acc_tables = []
    overall_acc_tables = []
    prrr_tables = []
    srrr_tables = []
    rank_prob_tables = []
    subset_accuracy_tables = []

    for dataset in sorted(scored_df["dataset"].unique()):
        dataset_df = scored_df.loc[scored_df["dataset"] == dataset].copy()
        score_array, item_order, model_order = build_score_array(dataset_df, f"Dataset {dataset}")
        subset_indices = sample_half_subsets(len(item_order), rng)
        subset_prompt_acc = compute_subset_prompt_accuracy(score_array, subset_indices)
        full_prompt_acc = score_array.mean(axis=0)

        prompt_acc_df, overall_acc_df = create_accuracy_tables(
            "dataset",
            dataset,
            model_order,
            score_array,
        )
        prrr_df, srrr_df, rank_prob_df = create_resampling_tables(
            "dataset",
            dataset,
            model_order,
            full_prompt_acc,
            subset_prompt_acc,
        )
        subset_accuracy_df = create_subset_accuracy_long(
            "dataset",
            dataset,
            model_order,
            subset_prompt_acc,
        )

        prompt_acc_tables.append(prompt_acc_df)
        overall_acc_tables.append(overall_acc_df)
        prrr_tables.append(prrr_df)
        srrr_tables.append(srrr_df)
        rank_prob_tables.append(rank_prob_df)
        subset_accuracy_tables.append(subset_accuracy_df)

        print(
            f"Analyzed {dataset}: {len(item_order)} items, subset size {len(item_order) // 2}, {len(model_order)} models."
        )

    prompt_acc_all = pd.concat(prompt_acc_tables, ignore_index=True)
    overall_acc_all = pd.concat(overall_acc_tables, ignore_index=True)
    prrr_all = pd.concat(prrr_tables, ignore_index=True)
    srrr_all = pd.concat(srrr_tables, ignore_index=True)
    rank_prob_all = pd.concat(rank_prob_tables, ignore_index=True)
    subset_accuracy_all = pd.concat(subset_accuracy_tables, ignore_index=True)

    prompt_acc_all.to_csv(ANALYSIS_DIR / "accuracy_by_dataset_model_prompt.csv", index=False)
    overall_acc_all.to_csv(ANALYSIS_DIR / "accuracy_by_dataset_model.csv", index=False)
    prrr_all.to_csv(ANALYSIS_DIR / "prompt_ranking_reversal_rate.csv", index=False)
    srrr_all.to_csv(ANALYSIS_DIR / "subset_ranking_reversal_rate.csv", index=False)
    rank_prob_all.to_csv(ANALYSIS_DIR / "rank_probability.csv", index=False)
    subset_accuracy_all.to_csv(ANALYSIS_DIR / "subset_accuracy_long.csv", index=False)

    plot_accuracy_boxplots(subset_accuracy_all)
    plot_prrr(prrr_all)
    plot_srrr(srrr_all)
    plot_rank_heatmaps(rank_prob_all)

    report_text = build_markdown_report(overall_acc_all, prrr_all, srrr_all, scored_df)
    (REPORTS_DIR / "analysis_summary.md").write_text(report_text, encoding="utf-8")

    print(f"Saved analysis tables to: {ANALYSIS_DIR}")
    print(f"Saved plots to: {PLOTS_DIR}")
    print(f"Saved report to: {REPORTS_DIR / 'analysis_summary.md'}")


if __name__ == "__main__":
    main()
