from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "03_scored" / "scored_results.csv"

RESAMPLE_ITERATIONS = 1000
BASE_TEMPLATE = "minimal_instruction"
TEMPLATE_ORDER = [
    "minimal_instruction",
    "benchmark_style",
    "natural_style",
    "order_phrasing_variation",
]
TEMPLATE_LABELS = {
    "minimal_instruction": "T1 Minimal",
    "benchmark_style": "T2 Benchmark",
    "natural_style": "T3 Natural",
    "order_phrasing_variation": "T4 Order/Phrasing",
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


def scope_label(scope_type: str, scope_value: str) -> str:
    if scope_type == "dataset":
        return DATASET_LABELS.get(scope_value, scope_value)
    return scope_value


def subset_size_for(n_items: int) -> int:
    subset_size = n_items // 2
    if subset_size < 1:
        raise ValueError(f"Need at least 2 items for half-split resampling, got {n_items}.")
    return subset_size


def build_score_array(subset: pd.DataFrame, scope_name: str):
    panel = subset.copy()
    panel["template_name"] = pd.Categorical(
        panel["template_name"], categories=TEMPLATE_ORDER, ordered=True
    )

    model_order = sorted(panel["model_id"].unique(), key=short_model_name)
    item_order = sorted(panel["item_id"].unique())

    pivot = (
        panel.pivot_table(
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
        raise ValueError(f"{scope_name} has {missing} missing score entries after pivot.")

    score_array = pivot.to_numpy(dtype=float).reshape(
        len(item_order), len(model_order), len(TEMPLATE_ORDER)
    )
    return score_array, item_order, model_order


def sample_half_subsets(n_items: int, rng: np.random.Generator) -> np.ndarray:
    subset_size = subset_size_for(n_items)
    return np.stack(
        [
            rng.choice(n_items, size=subset_size, replace=False)
            for _ in range(RESAMPLE_ITERATIONS)
        ],
        axis=0,
    )


def compute_subset_prompt_accuracy(
    score_array: np.ndarray, subset_indices: np.ndarray
) -> np.ndarray:
    sampled = score_array[subset_indices]
    return sampled.mean(axis=1)


def ranking_indices(score_vector: np.ndarray, model_order: list[str]) -> np.ndarray:
    ordered = sorted(
        range(len(model_order)),
        key=lambda idx: (-float(score_vector[idx]), short_model_name(model_order[idx])),
    )
    return np.asarray(ordered, dtype=int)


def ranking_matrix(score_matrix: np.ndarray, model_order: list[str]) -> np.ndarray:
    return np.vstack([ranking_indices(row, model_order) for row in score_matrix])


def create_accuracy_tables(
    scope_type: str,
    scope_value: str,
    model_order: list[str],
    score_array: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prompt_point = score_array.mean(axis=0)
    overall_point = score_array.mean(axis=(0, 2))

    prompt_rows = []
    for model_idx, model_id in enumerate(model_order):
        for template_idx, template_name in enumerate(TEMPLATE_ORDER):
            prompt_rows.append(
                {
                    "scope_type": scope_type,
                    "scope_value": scope_value,
                    "scope_label": scope_label(scope_type, scope_value),
                    "model_id": model_id,
                    "model_label": short_model_name(model_id),
                    "template_name": template_name,
                    "template_label": TEMPLATE_LABELS[template_name],
                    "accuracy": float(prompt_point[model_idx, template_idx]),
                }
            )

    ranking = ranking_indices(overall_point, model_order)
    rank_lookup = {model_order[idx]: position + 1 for position, idx in enumerate(ranking)}

    overall_rows = []
    for model_idx, model_id in enumerate(model_order):
        overall_rows.append(
            {
                "scope_type": scope_type,
                "scope_value": scope_value,
                "scope_label": scope_label(scope_type, scope_value),
                "model_id": model_id,
                "model_label": short_model_name(model_id),
                "accuracy": float(overall_point[model_idx]),
                "rank": rank_lookup[model_id],
            }
        )

    return pd.DataFrame(prompt_rows), pd.DataFrame(overall_rows)


def create_subset_accuracy_long(
    scope_type: str,
    scope_value: str,
    model_order: list[str],
    subset_prompt_acc: np.ndarray,
) -> pd.DataFrame:
    rows = []
    for model_idx, model_id in enumerate(model_order):
        for template_idx, template_name in enumerate(TEMPLATE_ORDER):
            for accuracy in subset_prompt_acc[:, model_idx, template_idx]:
                rows.append(
                    {
                        "scope_type": scope_type,
                        "scope_value": scope_value,
                        "scope_label": scope_label(scope_type, scope_value),
                        "model_id": model_id,
                        "model_label": short_model_name(model_id),
                        "template_name": template_name,
                        "template_label": TEMPLATE_LABELS[template_name],
                        "accuracy_pct": float(accuracy * 100),
                    }
                )
    return pd.DataFrame(rows)


def create_resampling_tables(
    scope_type: str,
    scope_value: str,
    model_order: list[str],
    full_prompt_acc: np.ndarray,
    subset_prompt_acc: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    full_orders = {
        template_name: ranking_indices(full_prompt_acc[:, template_idx], model_order)
        for template_idx, template_name in enumerate(TEMPLATE_ORDER)
    }
    subset_orders = {
        template_name: ranking_matrix(subset_prompt_acc[:, :, template_idx], model_order)
        for template_idx, template_name in enumerate(TEMPLATE_ORDER)
    }

    prrr_rows = []
    srrr_rows = []
    rank_prob_rows = []
    base_orders = subset_orders[BASE_TEMPLATE]

    for template_name in TEMPLATE_ORDER:
        orders = subset_orders[template_name]
        changed_vs_full = np.any(orders != full_orders[template_name], axis=1)
        srrr_rows.append(
            {
                "scope_type": scope_type,
                "scope_value": scope_value,
                "scope_label": scope_label(scope_type, scope_value),
                "template_name": template_name,
                "template_label": TEMPLATE_LABELS[template_name],
                "srrr": float(changed_vs_full.mean()),
            }
        )

        if template_name != BASE_TEMPLATE:
            changed_vs_base = np.any(orders != base_orders, axis=1)
            prrr_rows.append(
                {
                    "scope_type": scope_type,
                    "scope_value": scope_value,
                    "scope_label": scope_label(scope_type, scope_value),
                    "base_template_name": BASE_TEMPLATE,
                    "base_template_label": TEMPLATE_LABELS[BASE_TEMPLATE],
                    "compared_template_name": template_name,
                    "compared_template_label": TEMPLATE_LABELS[template_name],
                    "prrr": float(changed_vs_base.mean()),
                }
            )

        for position in range(len(model_order)):
            model_indices = orders[:, position]
            counts = np.bincount(model_indices, minlength=len(model_order))
            for model_idx, model_id in enumerate(model_order):
                rank_prob_rows.append(
                    {
                        "scope_type": scope_type,
                        "scope_value": scope_value,
                        "scope_label": scope_label(scope_type, scope_value),
                        "template_name": template_name,
                        "template_label": TEMPLATE_LABELS[template_name],
                        "model_id": model_id,
                        "model_label": short_model_name(model_id),
                        "rank_position": position + 1,
                        "probability": float(counts[model_idx] / len(model_indices)),
                    }
                )

    return (
        pd.DataFrame(prrr_rows),
        pd.DataFrame(srrr_rows),
        pd.DataFrame(rank_prob_rows),
    )
