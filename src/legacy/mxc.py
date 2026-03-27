"""Archived legacy scorer prototype. Kept for reference only."""

import re
from pathlib import Path

import pandas as pd





def load_input_csv(path: str) -> pd.DataFrame:
    
    
    df = pd.read_csv(path)

    
    
    required_cols = [
        "item_id",       
        "dataset",       
        "subject",       
        "split",         
        "question",      
        "choice_labels", 
        "choices",       
        "answer",        
        "model_id",      
        "raw_response",  
    ]

    
    
    missing = [c for c in required_cols if c not in df.columns]

    
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    return df





def normalize_text(text) -> str:
    

    
    
    if pd.isna(text):
        return ""

    
    text = str(text).strip()

    
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')

    
    
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text





def extract_answer(raw_response: str):
    

    
    text = normalize_text(raw_response)

    
    if not text:
        return None, "unparsed", "empty_text"

    
    
    t = text.upper()

    
    
    
    
    
    
    m = re.match(r"^\s*\[([^\]]+)\]", t)

    if m:
        
        
        
        
        content = m.group(1).strip()

        
        if re.fullmatch(r"[ABCD]", content):
            return content, "parsed", "leading_bracket_single"

        
        if re.fullmatch(r"[ABCD]{2,}", content):
            
            
            
            
            
            unique_letters = "".join(dict.fromkeys(content))

            
            
            if len(unique_letters) == 1:
                return unique_letters, "parsed", "leading_bracket_repeated"

            
            
            return None, "ambiguous", "leading_bracket_multi"

        
        return None, "unparsed", "leading_bracket_non_option"

    
    
    
    
    
    
    
    
    
    
    high_priority_patterns = [
        (r"FINAL ANSWER\s*[:=\-]?\s*\(?([ABCD])\)?", "final_answer"),
        (r"THE CORRECT ANSWER IS\s*\(?([ABCD])\)?", "correct_answer_is"),
        (r"CORRECT ANSWER\s*[:=\-]?\s*\(?([ABCD])\)?", "correct_answer"),
        (r"THE CORRECT OPTION IS\s*\(?([ABCD])\)?", "correct_option_is"),
        (r"CORRECT OPTION\s*[:=\-]?\s*\(?([ABCD])\)?", "correct_option"),
        (r"ANSWER IS\s*\(?([ABCD])\)?", "answer_is"),
        (r"ANSWER\s*[:=\-]?\s*\(?([ABCD])\)?", "answer_colon"),
        (r"I CHOOSE\s*\(?([ABCD])\)?", "i_choose"),
        (r"I PICK\s*\(?([ABCD])\)?", "i_pick"),
        (r"OPTION\s*\(?([ABCD])\)?", "option_letter"),
    ]

    
    for pattern, rule_name in high_priority_patterns:
        
        m = re.search(pattern, t)
        if m:
            
            return m.group(1), "parsed", rule_name

    
    
    
    
    
    
    
    compact = t.strip()

    
    if re.fullmatch(r"\(?[ABCD]\)?[\.]?", compact):
        m = re.search(r"([ABCD])", compact)
        if m:
            return m.group(1), "parsed", "compact_single_letter"

    
    
    
    
    
    
    candidates = re.findall(r"\b([ABCD])\b", t)

    
    
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)

    
    if len(seen) == 1:
        return seen[0], "parsed", "fallback_single_letter"

    
    elif len(seen) > 1:
        return None, "ambiguous", "fallback_multiple_letters"

    
    else:
        return None, "unparsed", "no_valid_option_found"





def score_prediction(pred_label, gold_label) -> int:
    

    
    
    if pred_label is None or pd.isna(gold_label):
        return 0

    
    
    return int(str(pred_label).upper() == str(gold_label).upper())





def main():
    

    
    
    
    input_path = Path("data/pilot_input.csv")

    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Cannot find input file: {input_path}\n"
            f"请把你的 CSV 放到这个路径，或者改这里的 input_path。"
        )

    
    df = load_input_csv(str(input_path))

    
    
    
    
    
    df = df.rename(columns={"answer": "gold_label"}).copy()

    
    
    
    
    
    parsed_results = df["raw_response"].apply(extract_answer)

    
    
    
    df["pred_label"] = parsed_results.apply(lambda x: x[0])

    
    
    
    
    
    df["parse_status"] = parsed_results.apply(lambda x: x[1])

    
    
    df["parse_rule"] = parsed_results.apply(lambda x: x[2])

    
    
    
    
    
    df["score"] = df.apply(
        lambda row: score_prediction(row["pred_label"], row["gold_label"]),
        axis=1,
    )

    
    
    
    
    
    preferred_cols = [
        "item_id",       
        "dataset",       
        "subject",       
        "split",         
        "model_id",      
        "gold_label",    
        "raw_response",  
        "pred_label",    
        "score",         
        "parse_status",  
        "parse_rule",    
        "question",      
        "choice_labels", 
        "choices",       
    ]

    
    
    out_cols = [c for c in preferred_cols if c in df.columns] + [
        c for c in df.columns if c not in preferred_cols
    ]

    scored_df = df[out_cols].copy()

    
    
    
    output_dir = Path("data")

    
    
    output_dir.mkdir(parents=True, exist_ok=True)

    scored_path = output_dir / "scored_results.csv"
    errors_path = output_dir / "parse_errors.csv"
    summary_path = output_dir / "parse_summary_by_model.csv"

    
    
    
    
    scored_df.to_csv(scored_path, index=False, encoding="utf-8-sig")

    
    
    
    
    
    error_df = scored_df[scored_df["parse_status"] != "parsed"].copy()
    error_df.to_csv(errors_path, index=False, encoding="utf-8-sig")

    
    
    
    
    
    
    
    
    
    summary_df = (
        scored_df.groupby(["model_id", "parse_status"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["model_id", "parse_status"])
    )
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    
    
    
    print(f"Saved: {scored_path}")
    print(f"Saved: {errors_path}")
    print(f"Saved: {summary_path}")
    print()

    print("=== Parse Status Summary ===")
    
    print(scored_df["parse_status"].value_counts(dropna=False))
    print()

    print("=== Accuracy by Model ===")
    
    
    model_acc = scored_df.groupby("model_id")["score"].mean().sort_values(ascending=False)
    print(model_acc)
    print()

    print("=== Overall Accuracy ===")
    
    print(scored_df["score"].mean())








if __name__ == "__main__":
    main()