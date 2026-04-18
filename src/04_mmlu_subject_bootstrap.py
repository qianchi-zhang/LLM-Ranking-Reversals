from __future__ import annotations

import ast
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from resampling_metrics import (
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
RAW_INPUT_CSV = BASE_DIR / "data" / "02_raw_responses_MMLU_subjects.csv"
SCORED_OUTPUT_DIR = BASE_DIR / "data" / "03_scored"
SCORED_OUTPUT_CSV = SCORED_OUTPUT_DIR / "mmlu_subjects_scored_results.csv"
PARSE_FAILURES_CSV = SCORED_OUTPUT_DIR / "mmlu_subjects_parse_failures.csv"
OUTPUT_DIR = BASE_DIR / "data" / "04_mmlu_subject_analysis_expanded"
PLOTS_DIR = BASE_DIR / "plots"
REPORTS_DIR = BASE_DIR / "reports"
REPORT_PATH = REPORTS_DIR / "mmlu_subject_bootstrap_summary_expanded.md"
SEED = 20260406
MMLU_SUBJECT_ORDER = [
    "high_school_mathematics",
    "conceptual_physics",
    "high_school_world_history",
    "philosophy",
    "sociology",
]
SUBJECT_SET_IDS = {
    subject: f"MMLU_S{index}"
    for index, subject in enumerate(MMLU_SUBJECT_ORDER, start=1)
}

OPTION_PATTERNS = [
    re.compile(r"^\s*[\(\[]?\s*([A-D])\s*[\)\]]?\s*$", re.IGNORECASE),
    re.compile(
        r"\b(?:answer|correct answer|best answer|option|choice)\b[^A-D]{0,20}[\(\[]?\s*([A-D])\s*[\)\]]?",
        re.IGNORECASE,
    ),
    re.compile(r"(?<![A-Z])([A-D])(?![A-Z])", re.IGNORECASE),
]


def parse_metadata(value):
    if pd.isna(value):
        return {}
    if isinstance(value, dict):
        return value
    text = str(value).strip()
    if not text:
        return {}
    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def normalize_option(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().upper()
    if not text:
        return None
    match = re.fullmatch(r"[\(\[]?\s*([A-D])\s*[\)\]]?", text)
    if match:
        return match.group(1)
    return None


def extract_option(raw_response):
    if raw_response is None or pd.isna(raw_response):
        return None, "missing"

    text = str(raw_response).strip()
    if not text:
        return None, "empty"

    for index, pattern in enumerate(OPTION_PATTERNS):
        matches = pattern.findall(text)
        if not matches:
            continue

        if index == 2:
            unique_matches = sorted({match.upper() for match in matches})
            if len(unique_matches) == 1:
                return unique_matches[0], "token_match"
            return None, "ambiguous_token_match"

        return matches[0].upper(), f"pattern_{index + 1}"

    return None, "unparsed"


def build_scored_results(df: pd.DataFrame) -> pd.DataFrame:
    metadata = df["metadata"].apply(parse_metadata)
    gold_answers = metadata.apply(lambda item: normalize_option(item.get("gold_answer")))

    parsed = df["raw_response"].apply(extract_option)
    parsed_answers = parsed.apply(lambda item: item[0])
    parse_methods = parsed.apply(lambda item: item[1])

    scored = df.copy()
    scored["gold_answer"] = gold_answers
    scored["parsed_answer"] = parsed_answers
    scored["parse_method"] = parse_methods
    scored["is_parsed"] = scored["parsed_answer"].notna()
    scored["score"] = (
        (scored["parsed_answer"] == scored["gold_answer"]) & scored["gold_answer"].notna()
    ).astype(int)
    return scored


def sanitize_subject_name(subject: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", subject.lower())


def add_subject_metadata(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["subject_set_id"] = enriched["scope_value"].map(SUBJECT_SET_IDS)
    enriched["subject_name"] = enriched["scope_value"]
    enriched["scope_label"] = enriched["subject_set_id"] + " (" + enriched["subject_name"] + ")"
    return enriched


def ordered_subject_values(df: pd.DataFrame) -> list[str]:
    return [subject for subject in MMLU_SUBJECT_ORDER if subject in set(df["scope_value"])]


def ordered_subject_labels(df: pd.DataFrame) -> list[str]:
    scope_to_label = (
        df[["scope_value", "scope_label"]]
        .drop_duplicates()
        .set_index("scope_value")["scope_label"]
    )
    return [scope_to_label[subject] for subject in ordered_subject_values(df)]


def plot_subject_accuracy_boxplots(subject_subset_accuracy: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    subjects = ordered_subject_values(subject_subset_accuracy)
    model_labels = sorted(subject_subset_accuracy["model_label"].unique())
    fig = plt.figure(figsize=(18, 10))
    grid = fig.add_gridspec(2, 6)
    axes = [
        fig.add_subplot(grid[0, 0:2]),
        fig.add_subplot(grid[0, 2:4]),
        fig.add_subplot(grid[0, 4:6]),
        fig.add_subplot(grid[1, 1:3]),
        fig.add_subplot(grid[1, 3:5]),
    ]

    shared_axis = axes[0]
    for axis in axes[1:]:
        axis.sharey(shared_axis)

    color_map = plt.get_cmap("tab10", len(model_labels))
    offsets = np.linspace(-0.27, 0.27, len(model_labels))
    width = 0.16

    for axis, subject in zip(axes, subjects):
        subset = subject_subset_accuracy.loc[subject_subset_accuracy["scope_value"] == subject]
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

        axis.set_title(f"{SUBJECT_SET_IDS[subject]}\n{subject}", fontsize=10)
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
    fig.savefig(
        PLOTS_DIR / "mmlu_subject_expanded_accuracy_boxplots.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def plot_subject_prrr(subject_prrr: pd.DataFrame) -> None:
    plt.style.use("ggplot")
    x_labels = ordered_subject_labels(subject_prrr)
    compared_labels = [
        TEMPLATE_LABELS[name] for name in TEMPLATE_ORDER if name != TEMPLATE_ORDER[0]
    ]
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

    ax.set_title("Expanded MMLU Subject-Level PRRR")
    ax.set_xlabel("Subject")
    ax.set_ylabel("PRRR")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_expanded_prrr.png", dpi=300, bbox_inches="tight")
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

    ax.set_title("Expanded MMLU Subject-Level SRRR")
    ax.set_xlabel("Subject")
    ax.set_ylabel("SRRR")
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=20, ha="right")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "mmlu_subject_expanded_srrr.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_rank_heatmaps(rank_probs: pd.DataFrame) -> None:
    plt.style.use("default")
    for subject in ordered_subject_values(rank_probs):
        subset = rank_probs.loc[rank_probs["scope_value"] == subject]
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

        label = f"{SUBJECT_SET_IDS[subject]} - {subject}"
        fig.suptitle(f"Rank Probability - {label}", y=0.98)
        if image is not None:
            fig.colorbar(image, ax=axes, shrink=0.85, location="right")
        fig.savefig(
            PLOTS_DIR / f"mmlu_subject_expanded_{SUBJECT_SET_IDS[subject]}_rank_probability_heatmaps.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close(fig)


def build_report(
    scored_df: pd.DataFrame,
    subject_overall: pd.DataFrame,
    subject_prrr: pd.DataFrame,
    subject_srrr: pd.DataFrame,
) -> str:
    lines = [
        "# Expanded MMLU Subject Resampling Summary",
        "",
        "## Scope",
        "",
        "- Data source: `data/02_raw_responses_MMLU_subjects.csv` scored into `data/03_scored/mmlu_subjects_scored_results.csv`.",
        "- Subjects analyzed: `high_school_mathematics`, `conceptual_physics`, `high_school_world_history`, `philosophy`, `sociology`.",
        "- Items per subject: 200.",
        f"- Resampling iterations per subject: {RESAMPLE_ITERATIONS}.",
        "- Each subject subset uses 100 items drawn without replacement from that subject's 200-item pool.",
        "",
        "## Data Check",
        "",
        f"- Total scored rows: {len(scored_df)}.",
        f"- Parse failures: {(~scored_df['is_parsed']).sum()} rows.",
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
            "- `data/03_scored/mmlu_subjects_scored_results.csv`",
            "- `data/03_scored/mmlu_subjects_parse_failures.csv`",
            "- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_overall_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_prompt_accuracy.csv`",
            "- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_prompt_ranking_reversal_rate.csv`",
            "- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_subset_ranking_reversal_rate.csv`",
            "- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_rank_probability.csv`",
            "- `data/04_mmlu_subject_analysis_expanded/mmlu_subject_subset_accuracy_long.csv`",
            "- `plots/mmlu_subject_expanded_accuracy_boxplots.png`",
            "- `plots/mmlu_subject_expanded_prrr.png`",
            "- `plots/mmlu_subject_expanded_srrr.png`",
            "- `plots/mmlu_subject_expanded_*_rank_probability_heatmaps.png`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    if not RAW_INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {RAW_INPUT_CSV}")

    SCORED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_df = pd.read_csv(RAW_INPUT_CSV)
    required_columns = {"item_id", "dataset", "subject", "template_name", "model_id", "raw_response", "metadata"}
    missing_columns = required_columns - set(raw_df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns in raw input: {sorted(missing_columns)}")

    scored_df = build_scored_results(raw_df)
    scored_df.to_csv(SCORED_OUTPUT_CSV, index=False)
    scored_df.loc[~scored_df["is_parsed"]].to_csv(PARSE_FAILURES_CSV, index=False)

    rng = np.random.default_rng(SEED)

    prompt_tables = []
    overall_tables = []
    prrr_tables = []
    srrr_tables = []
    rank_prob_tables = []
    subset_accuracy_tables = []

    for subject in MMLU_SUBJECT_ORDER:
        subject_df = scored_df.loc[scored_df["subject"] == subject].copy()
        if subject_df.empty:
            raise ValueError(f"Subject {subject} not found in {RAW_INPUT_CSV.name}.")

        item_count = subject_df["item_id"].nunique()
        if item_count != 200:
            raise ValueError(f"Subject {subject} expected 200 items, found {item_count}.")

        score_array, item_order, model_order = build_score_array(
            subject_df,
            f"Expanded MMLU subject {subject}",
        )
        subset_indices = sample_half_subsets(len(item_order), rng)
        subset_prompt_acc = compute_subset_prompt_accuracy(score_array, subset_indices)
        full_prompt_acc = score_array.mean(axis=0)

        prompt_df, overall_df = create_accuracy_tables(
            "mmlu_subject_expanded",
            subject,
            model_order,
            score_array,
        )
        prrr_df, srrr_df, rank_prob_df = create_resampling_tables(
            "mmlu_subject_expanded",
            subject,
            model_order,
            full_prompt_acc,
            subset_prompt_acc,
        )
        subset_accuracy_df = create_subset_accuracy_long(
            "mmlu_subject_expanded",
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
            f"Analyzed {subject}: {len(item_order)} items, subset size {len(item_order) // 2}, {len(model_order)} models."
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

    plot_subject_accuracy_boxplots(subject_subset_accuracy)
    plot_subject_prrr(subject_prrr)
    plot_subject_srrr(subject_srrr)
    plot_rank_heatmaps(subject_rank_prob)

    report = build_report(scored_df, subject_overall, subject_prrr, subject_srrr)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Saved scored results to: {SCORED_OUTPUT_CSV}")
    print(f"Saved parse failures to: {PARSE_FAILURES_CSV}")
    print(f"Saved expanded MMLU subject analysis to: {OUTPUT_DIR}")
    print(f"Saved plots to: {PLOTS_DIR}")
    print(f"Saved report to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
