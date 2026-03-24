from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "03_scored" / "scored_results.csv"
ANALYSIS_DIR = BASE_DIR / "data" / "04_analysis"
PLOTS_DIR = BASE_DIR / "plots"
REPORTS_DIR = BASE_DIR / "reports"

BOOTSTRAP_ITERATIONS = 2000
SEED = 20260324
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
DATASET_LABELS = {
    "mmlu": "MMLU",
    "arc_challenge": "ARC-Challenge",
    "hellaswag": "HellaSwag",
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


def pivot_dataset_scores(df: pd.DataFrame, dataset: str):
    subset = df.loc[df["dataset"] == dataset].copy()
    subset["template_name"] = pd.Categorical(
        subset["template_name"], categories=TEMPLATE_ORDER, ordered=True
    )

    model_order = sorted(subset["model_id"].unique(), key=short_model_name)
    item_order = sorted(subset["item_id"].unique())

    pivot = (
        subset.pivot_table(
            index="item_id",
            columns=["model_id", "template_name"],
            values="score",
            aggfunc="first",
        )
        .reindex(item_order)
        .sort_index(axis=1, level=[0, 1])
    )

    column_index = pd.MultiIndex.from_product(
        [model_order, TEMPLATE_ORDER], names=["model_id", "template_name"]
    )
    pivot = pivot.reindex(columns=column_index)

    if pivot.isna().any().any():
        missing = int(pivot.isna().sum().sum())
        raise ValueError(f"Dataset {dataset} has {missing} missing score entries after pivot.")

    score_array = pivot.to_numpy(dtype=float).reshape(len(item_order), len(model_order), len(TEMPLATE_ORDER))
    return score_array, item_order, model_order


def bootstrap_dataset(score_array: np.ndarray, rng: np.random.Generator):
    n_items = score_array.shape[0]
    sample_idx = rng.integers(0, n_items, size=(BOOTSTRAP_ITERATIONS, n_items))
    sampled = score_array[sample_idx]
    boot_prompt_acc = sampled.mean(axis=1)
    boot_overall_acc = sampled.mean(axis=(1, 3))
    return boot_prompt_acc, boot_overall_acc


def create_accuracy_tables(dataset, model_order, score_array, boot_prompt_acc, boot_overall_acc):
    prompt_point = score_array.mean(axis=0)
    overall_point = score_array.mean(axis=(0, 2))

    prompt_rows = []
    for model_idx, model_id in enumerate(model_order):
        for template_idx, template_name in enumerate(TEMPLATE_ORDER):
            ci_low, ci_high = percentile_ci(boot_prompt_acc[:, model_idx, template_idx])
            prompt_rows.append(
                {
                    "dataset": dataset,
                    "dataset_label": DATASET_LABELS.get(dataset, dataset),
                    "model_id": model_id,
                    "model_label": short_model_name(model_id),
                    "template_name": template_name,
                    "template_label": TEMPLATE_LABELS[template_name],
                    "accuracy": float(prompt_point[model_idx, template_idx]),
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                }
            )

    overall_rows = []
    ranking = sorted(
        range(len(model_order)),
        key=lambda idx: (-overall_point[idx], short_model_name(model_order[idx])),
    )
    rank_lookup = {model_order[idx]: rank + 1 for rank, idx in enumerate(ranking)}
    for model_idx, model_id in enumerate(model_order):
        ci_low, ci_high = percentile_ci(boot_overall_acc[:, model_idx])
        overall_rows.append(
            {
                "dataset": dataset,
                "dataset_label": DATASET_LABELS.get(dataset, dataset),
                "model_id": model_id,
                "model_label": short_model_name(model_id),
                "accuracy": float(overall_point[model_idx]),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "rank": rank_lookup[model_id],
            }
        )
    return pd.DataFrame(prompt_rows), pd.DataFrame(overall_rows)


def create_pairwise_significance_table(dataset, model_order, boot_overall_acc, score_array):
    overall_point = score_array.mean(axis=(0, 2))
    rows = []
    for left_idx, right_idx in combinations(range(len(model_order)), 2):
        left_model = model_order[left_idx]
        right_model = model_order[right_idx]
        diff = boot_overall_acc[:, left_idx] - boot_overall_acc[:, right_idx]
        ci_low, ci_high = percentile_ci(diff)
        point_diff = float(overall_point[left_idx] - overall_point[right_idx])
        p_value = bootstrap_p_value(diff)
        rows.append(
            {
                "dataset": dataset,
                "left_model_id": left_model,
                "left_model_label": short_model_name(left_model),
                "right_model_id": right_model,
                "right_model_label": short_model_name(right_model),
                "point_diff": point_diff,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "p_value": p_value,
                "significant_95": not (ci_low <= 0 <= ci_high),
                "left_win_rate": float(np.mean(diff > 0) + 0.5 * np.mean(diff == 0)),
            }
        )
    return pd.DataFrame(rows)


def create_rrr_and_rank_probs(dataset, model_order, boot_prompt_acc):
    order_matrices = {
        template: make_order_matrix(boot_prompt_acc[:, :, template_idx])
        for template_idx, template in enumerate(TEMPLATE_ORDER)
    }
    base_orders = order_matrices[BASE_TEMPLATE]

    rrr_rows = []
    rank_prob_rows = []

    for template_name, orders in order_matrices.items():
        changed = np.any(orders != base_orders, axis=1)
        if template_name != BASE_TEMPLATE:
            rrr_rows.append(
                {
                    "dataset": dataset,
                    "dataset_label": DATASET_LABELS.get(dataset, dataset),
                    "template_name": template_name,
                    "template_label": TEMPLATE_LABELS[template_name],
                    "rrr": float(changed.mean()),
                }
            )

        for position in range(len(model_order)):
            model_indices = orders[:, position]
            counts = np.bincount(model_indices, minlength=len(model_order))
            for model_idx, model_id in enumerate(model_order):
                rank_prob_rows.append(
                    {
                        "dataset": dataset,
                        "dataset_label": DATASET_LABELS.get(dataset, dataset),
                        "template_name": template_name,
                        "template_label": TEMPLATE_LABELS[template_name],
                        "model_id": model_id,
                        "model_label": short_model_name(model_id),
                        "rank_position": position + 1,
                        "probability": float(counts[model_idx] / len(model_indices)),
                    }
                )

    return pd.DataFrame(rrr_rows), pd.DataFrame(rank_prob_rows)


def create_bootstrap_long_df(dataset, model_order, boot_prompt_acc):
    rows = []
    for model_idx, model_id in enumerate(model_order):
        for template_idx, template_name in enumerate(TEMPLATE_ORDER):
            series = boot_prompt_acc[:, model_idx, template_idx]
            for accuracy in series:
                rows.append(
                    {
                        "dataset": dataset,
                        "dataset_label": DATASET_LABELS.get(dataset, dataset),
                        "model_id": model_id,
                        "model_label": short_model_name(model_id),
                        "template_name": template_name,
                        "template_label": TEMPLATE_LABELS[template_name],
                        "accuracy_pct": float(accuracy * 100),
                    }
                )
    return pd.DataFrame(rows)


def plot_accuracy_boxplots(bootstrap_long: pd.DataFrame):
    plt.style.use("ggplot")
    datasets = sorted(bootstrap_long["dataset"].unique())
    model_labels = sorted(bootstrap_long["model_label"].unique())
    fig, axes = plt.subplots(1, len(datasets), figsize=(18, 6), sharey=True)
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])

    color_map = plt.get_cmap("tab10", len(model_labels))
    offsets = np.linspace(-0.27, 0.27, len(model_labels))
    width = 0.16

    for axis, dataset in zip(axes, datasets):
        subset = bootstrap_long.loc[bootstrap_long["dataset"] == dataset]
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
        axis.set_xlabel("Prompt Template")
        axis.set_ylabel("Bootstrap Accuracy (%)")
        axis.set_xticks(positions)
        axis.set_xticklabels([TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER], rotation=20)

    handles = [
        plt.Line2D([0], [0], color=color_map(idx), lw=8, alpha=0.8)
        for idx in range(len(model_labels))
    ]
    fig.legend(handles, model_labels, loc="upper center", ncol=4, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    output_path = PLOTS_DIR / "accuracy_boxplots.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_rrr(rrr_df: pd.DataFrame):
    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(10, 6))
    dataset_labels = [DATASET_LABELS[key] for key in sorted(rrr_df["dataset"].unique())]
    template_labels = [TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER if name != BASE_TEMPLATE]
    pivot = (
        rrr_df.pivot(index="dataset_label", columns="template_label", values="rrr")
        .reindex(dataset_labels)
        .reindex(columns=template_labels)
    )
    x = np.arange(len(dataset_labels))
    offsets = np.linspace(-0.25, 0.25, len(template_labels))
    bar_width = 0.22

    for idx, template_label in enumerate(template_labels):
        ax.bar(x + offsets[idx], pivot[template_label].to_numpy(), width=bar_width, label=template_label)

    ax.set_xlabel("Dataset")
    ax.set_ylabel("Ranking Reversal Rate")
    ax.set_ylim(0, 1)
    ax.set_xticks(x)
    ax.set_xticklabels(dataset_labels)
    ax.legend(title="Compared Prompt", frameon=False)
    fig.tight_layout()
    output_path = PLOTS_DIR / "ranking_reversal_rate.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_rank_heatmaps(rank_probs: pd.DataFrame):
    plt.style.use("default")
    for dataset in sorted(rank_probs["dataset"].unique()):
        subset = rank_probs.loc[rank_probs["dataset"] == dataset]
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
            image = axis.imshow(pivot.to_numpy(), cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
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

        fig.suptitle(f"Rank Probability Heatmaps - {DATASET_LABELS.get(dataset, dataset)}", y=0.98)
        if image is not None:
            fig.colorbar(image, ax=axes, shrink=0.85, location="right")
        output_path = PLOTS_DIR / f"{dataset}_rank_probability_heatmaps.png"
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)


def build_markdown_report(
    overall_acc_df: pd.DataFrame,
    prompt_acc_df: pd.DataFrame,
    pairwise_df: pd.DataFrame,
    rrr_df: pd.DataFrame,
    scored_df: pd.DataFrame,
):
    lines = [
        "# Analysis Summary",
        "",
        "## Scope",
        "",
        "- Data source: `data/02_raw_responses.csv` scored into `data/03_scored/scored_results.csv`.",
        f"- Bootstrap iterations: {BOOTSTRAP_ITERATIONS}.",
        f"- Baseline prompt for RRR: `{BASE_TEMPLATE}`.",
        "",
        "## Key Findings",
        "",
    ]

    parse_failures = int((~scored_df["is_parsed"]).sum())
    refusal_rate = parse_failures / len(scored_df)
    lines.append(f"- Parse failures were rare: {parse_failures} / {len(scored_df)} rows ({refusal_rate:.2%}).")

    for dataset in sorted(overall_acc_df["dataset"].unique()):
        dataset_overall = overall_acc_df.loc[overall_acc_df["dataset"] == dataset].sort_values("rank")
        winner = dataset_overall.iloc[0]
        runner_up = dataset_overall.iloc[1]
        lines.append(
            "- "
            f"{DATASET_LABELS.get(dataset, dataset)} winner: {winner['model_label']} "
            f"({winner['accuracy']:.2%}, 95% CI [{winner['ci_low']:.2%}, {winner['ci_high']:.2%}]); "
            f"runner-up: {runner_up['model_label']} ({runner_up['accuracy']:.2%})."
        )

        dataset_rrr = rrr_df.loc[rrr_df["dataset"] == dataset].sort_values("rrr", ascending=False)
        most_unstable = dataset_rrr.iloc[0]
        least_unstable = dataset_rrr.iloc[-1]
        lines.append(
            "- "
            f"{DATASET_LABELS.get(dataset, dataset)} ranking was most unstable under "
            f"{most_unstable['template_label']} (RRR={most_unstable['rrr']:.2%}) and most stable under "
            f"{least_unstable['template_label']} (RRR={least_unstable['rrr']:.2%})."
        )

        dataset_pairs = pairwise_df.loc[pairwise_df["dataset"] == dataset]
        sig_pairs = dataset_pairs.loc[dataset_pairs["significant_95"]].sort_values("point_diff", ascending=False)
        if sig_pairs.empty:
            lines.append(f"- {DATASET_LABELS.get(dataset, dataset)} had no pairwise model differences with 95% bootstrap support.")
        else:
            top_sig = sig_pairs.iloc[0]
            lines.append(
                "- "
                f"Strongest supported gap on {DATASET_LABELS.get(dataset, dataset)}: "
                f"{top_sig['left_model_label']} vs {top_sig['right_model_label']} = {top_sig['point_diff']:.2%} "
                f"(95% CI [{top_sig['ci_low']:.2%}, {top_sig['ci_high']:.2%}], p={top_sig['p_value']:.4f})."
            )

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "- Report both absolute accuracy and ranking stability. A model that wins on point estimate but has high RRR should not be described as robust without qualification.",
            "- Use prompt-averaged accuracy for the main leaderboard and keep prompt-specific results in the appendix. This reduces over-reading a single prompt formulation.",
            "- Flag safety-refusal and parse-failure rows explicitly in the paper, because they are rare here but can distort benchmark conclusions when concentrated in one model family.",
            "- When discussing top-vs-second differences, rely on bootstrap confidence intervals instead of raw ranking alone, especially on datasets where the leading pair is close.",
            "",
            "## Output Files",
            "",
            "- `data/04_analysis/accuracy_by_dataset_model.csv`",
            "- `data/04_analysis/accuracy_by_dataset_model_prompt.csv`",
            "- `data/04_analysis/pairwise_significance.csv`",
            "- `data/04_analysis/ranking_reversal_rate.csv`",
            "- `data/04_analysis/rank_probability.csv`",
            "- `plots/accuracy_boxplots.png`",
            "- `plots/ranking_reversal_rate.png`",
            "- `plots/*_rank_probability_heatmaps.png`",
        ]
    )

    return "\n".join(lines) + "\n"


def main():
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
    pairwise_tables = []
    rrr_tables = []
    rank_prob_tables = []
    bootstrap_long_tables = []

    for dataset in sorted(scored_df["dataset"].unique()):
        score_array, item_order, model_order = pivot_dataset_scores(scored_df, dataset)
        expected_items = len(item_order)
        print(f"Analyzing {dataset}: {expected_items} items, {len(model_order)} models, {len(TEMPLATE_ORDER)} prompts")

        boot_prompt_acc, boot_overall_acc = bootstrap_dataset(score_array, rng)
        prompt_acc_df, overall_acc_df = create_accuracy_tables(
            dataset, model_order, score_array, boot_prompt_acc, boot_overall_acc
        )
        pairwise_df = create_pairwise_significance_table(dataset, model_order, boot_overall_acc, score_array)
        rrr_df, rank_prob_df = create_rrr_and_rank_probs(dataset, model_order, boot_prompt_acc)
        bootstrap_long_df = create_bootstrap_long_df(dataset, model_order, boot_prompt_acc)

        prompt_acc_tables.append(prompt_acc_df)
        overall_acc_tables.append(overall_acc_df)
        pairwise_tables.append(pairwise_df)
        rrr_tables.append(rrr_df)
        rank_prob_tables.append(rank_prob_df)
        bootstrap_long_tables.append(bootstrap_long_df)

    prompt_acc_all = pd.concat(prompt_acc_tables, ignore_index=True)
    overall_acc_all = pd.concat(overall_acc_tables, ignore_index=True)
    pairwise_all = pd.concat(pairwise_tables, ignore_index=True)
    rrr_all = pd.concat(rrr_tables, ignore_index=True)
    rank_prob_all = pd.concat(rank_prob_tables, ignore_index=True)
    bootstrap_long_all = pd.concat(bootstrap_long_tables, ignore_index=True)

    prompt_acc_all.to_csv(ANALYSIS_DIR / "accuracy_by_dataset_model_prompt.csv", index=False)
    overall_acc_all.to_csv(ANALYSIS_DIR / "accuracy_by_dataset_model.csv", index=False)
    pairwise_all.to_csv(ANALYSIS_DIR / "pairwise_significance.csv", index=False)
    rrr_all.to_csv(ANALYSIS_DIR / "ranking_reversal_rate.csv", index=False)
    rank_prob_all.to_csv(ANALYSIS_DIR / "rank_probability.csv", index=False)
    bootstrap_long_all.to_csv(ANALYSIS_DIR / "bootstrap_accuracy_long.csv", index=False)

    plot_accuracy_boxplots(bootstrap_long_all)
    plot_rrr(rrr_all)
    plot_rank_heatmaps(rank_prob_all)

    report_text = build_markdown_report(
        overall_acc_all, prompt_acc_all, pairwise_all, rrr_all, scored_df
    )
    (REPORTS_DIR / "analysis_summary.md").write_text(report_text, encoding="utf-8")

    print(f"Saved analysis tables to: {ANALYSIS_DIR}")
    print(f"Saved plots to: {PLOTS_DIR}")
    print(f"Saved report to: {REPORTS_DIR / 'analysis_summary.md'}")


if __name__ == "__main__":
    main()
