"""Phase 3 scorer for fixed Phase 2 responses.

This script parses the already-collected API outputs in `data/02_raw_responses.csv`
and converts each response into a single binary `score`. Any later subset
resampling in Phase 4 reuses these fixed scores and does not send new API
requests.
"""

import ast
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_CSV = BASE_DIR / "data" / "02_raw_responses.csv"
OUTPUT_DIR = BASE_DIR / "data" / "03_scored"
OUTPUT_CSV = OUTPUT_DIR / "scored_results.csv"
PARSE_FAILURES_CSV = OUTPUT_DIR / "parse_failures.csv"

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


def build_scored_results(df):
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


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV)
    scored = build_scored_results(df)

    scored.to_csv(OUTPUT_CSV, index=False)
    scored.loc[~scored["is_parsed"]].to_csv(PARSE_FAILURES_CSV, index=False)

    total_rows = len(scored)
    parse_failures = int((~scored["is_parsed"]).sum())
    overall_accuracy = float(scored["score"].mean())

    print(f"Saved scored results to: {OUTPUT_CSV}")
    print(f"Saved parse failures to: {PARSE_FAILURES_CSV}")
    print(f"Rows: {total_rows}")
    print(f"Parse failures: {parse_failures} ({parse_failures / total_rows:.2%})")
    print(f"Overall accuracy: {overall_accuracy:.2%}")


if __name__ == "__main__":
    main()
