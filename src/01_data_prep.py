import json
import random
from pathlib import Path
from datasets import load_dataset

SEED = 114514
random.seed(SEED)


# Selected 6 subjects for MMLU
MMLU_SUBJECTS = [
    "formal_logic",
    "high_school_macroeconomics",
    "college_medicine",
    "high_school_physics",
    "philosophy",
    "international_law",
]

MMLU_N_PER_SUBJECT = 50
ARC_N = 300
HELLASWAG_N = 300

# TODO
MODEL_NAME = "openai/gpt-5.2"

'''
TEMPLATES = {
    "minimal_instruction": (
        "{question}\n\n"
        "{choices_block}\n\n"
        "Respond with one letter only (A/B/C/D)."
    ),
    "benchmark_style": (
        "Please answer the following multiple choice question by selecting the single best option.\n\n"
        "Question:\n{question}\n\n"
        "Options:\n{choices_block}\n\n"
        "Respond with one letter only (A/B/C/D)."
    ),
    "minor_nonsemantic": (
        "Please answer the following multiple-choice question by selecting the single best option:\n"
        "Question--\n{question}\n"
        "Options--\n{choices_block}\n"
        "Respond with one letter only ( A / B / C / D )"
    ),
    "order_phrasing_variation": (
        "Respond using one letter among \"A\", \"B\", \"C\", or \"D\" only.\n\n"
        "Question:\n{question}\n\n"
        "Options:\n{choices_block}\n\n"
        "Please select the best answer for the multiple choice question given above."
    ),
}
'''

TEMPLATES = {

    "minimal_instruction": (
        "{question}\n\n"
        "{choices_block}\n\n"
        #"Your answer should be ONE letter only (A, B, C, or D)."
    ),

    "benchmark_style": (
        "Choose the correct answer to the following multiple-choice question.\n\n"
        "Question:\n{question}\n\n"
        "Options:\n{choices_block}\n\n"
        #"Answer with one letter (A, B, C, or D)."
    ),

    "natural_style": (
        "Here is a multiple-choice question.\n\n"
        "{question}\n\n"
        "{choices_block}\n\n"
        #"Which option is correct? Reply with one letter only (A, B, C, or D)."
        "Which option is correct?"
    ),

    "order_phrasing_variation": (
        #"Reply with only ONE letter corresponding to the correct answer (A, B, C, or D).\n\n"
        "Select the best option."
        "{question}\n\n"
        "{choices_block}\n\n"
        "Above is a question with four possible options.\n\n"
    ),
}


def choice_labels_for_n(n):
    return [chr(ord("A") + i) for i in range(n)]

def build_choices_block(labels, choices):
    return "\n".join(f"{lab}. {txt}" for lab, txt in zip(labels, choices))

def save_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


# MMLU：50 items for each of the 6 subjects, 300 in total
def sample_mmlu(subjects, n_per_subject=MMLU_N_PER_SUBJECT, seed=SEED):
    rows = []

    for subject in subjects:
        ds = load_dataset("cais/mmlu", subject, split="test")
        ds = ds.shuffle(seed=seed)

        if len(ds) < n_per_subject:
            raise ValueError(f"MMLU subject {subject} only has {len(ds)} items in test split")

        ds = ds.select(range(n_per_subject))

        for i, ex in enumerate(ds):
            choices = ex["choices"]
            labels = choice_labels_for_n(len(choices))
            answer = labels[ex["answer"]] if isinstance(ex["answer"], int) else str(ex["answer"])

            rows.append({
                "item_id": f"mmlu_{subject}_{i:04d}",
                "dataset": "mmlu",
                "subject": subject,
                "split": "test",
                "question": ex["question"],
                "choice_labels": labels,
                "choices": choices,
                "answer": answer,
            })

    return rows


# ARC-Challenge：300 items
def sample_arc(n=ARC_N, seed=SEED):
    ds = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test")
    ds = ds.shuffle(seed=seed)

    if len(ds) < n:
        raise ValueError(f"ARC-Challenge test split only has {len(ds)} items")

    ds = ds.select(range(n))
    rows = []

    for i, ex in enumerate(ds):
        rows.append({
            "item_id": f"arc_challenge_{i:04d}",
            "dataset": "arc_challenge",
            "subject": None,
            "split": "test",
            "question": ex["question"],
            "choice_labels": ex["choices"]["label"],
            "choices": ex["choices"]["text"],
            "answer": ex["answerKey"],
        })

    return rows


# HellaSwag：300 items from validation split (test split does not provide answer)
def sample_hellaswag(n=HELLASWAG_N, seed=SEED, split="validation"):
    ds = load_dataset("Rowan/hellaswag", split=split)
    ds = ds.shuffle(seed=seed)

    if len(ds) < n:
        raise ValueError(f"HellaSwag {split} split only has {len(ds)} items")

    ds = ds.select(range(n))
    rows = []

    for i, ex in enumerate(ds):
        labels = choice_labels_for_n(len(ex["endings"]))
        answer = labels[int(ex["label"])]

        rows.append({
            "item_id": f"hellaswag_{i:04d}",
            "dataset": "hellaswag",
            "subject": None,
            "split": split,
            "question": ex["ctx"],
            "choice_labels": labels,
            "choices": ex["endings"],
            "answer": answer,
        })

    return rows


def expand_to_prompt_requests(items, model_name):
    reqs = []

    for item in items:
        choices_block = build_choices_block(item["choice_labels"], item["choices"])

        for template_name, template in TEMPLATES.items():
            prompt = template.format(
                question=item["question"],
                choices_block=choices_block
            )

            reqs.append({
                "request_id": f"{item['item_id']}__{template_name}",
                "item_id": item["item_id"],
                "dataset": item["dataset"],
                "subject": item["subject"],
                "split": item["split"],
                "template_name": template_name,
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "metadata": {
                    "gold_answer": item["answer"]
                }
            })

    return reqs



def main():
    mmlu_items = sample_mmlu(MMLU_SUBJECTS, n_per_subject=MMLU_N_PER_SUBJECT, seed=SEED)
    arc_items = sample_arc(n=ARC_N, seed=SEED)
    hellaswag_items = sample_hellaswag(n=HELLASWAG_N, seed=SEED, split="validation")

    all_items = mmlu_items + arc_items + hellaswag_items
    all_requests = expand_to_prompt_requests(all_items, model_name=MODEL_NAME)

    # items.jsonl for og questions, requests,jsonl for templated prompts
    save_jsonl("data/00_raw_question.jsonl", all_items)
    save_jsonl("data/01_prompts.jsonl", all_requests)

    print(f"Total items: {len(all_items)}")
    print(f"Total prompt requests: {len(all_requests)}")

if __name__ == "__main__":
    main()