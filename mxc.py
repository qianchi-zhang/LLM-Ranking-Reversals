import re
from pathlib import Path

import pandas as pd


# =========================================================
# 1. 读取输入 CSV
# =========================================================
def load_input_csv(path: str) -> pd.DataFrame:
    """
    作用：
        读取输入的 CSV 文件，并检查它是否包含我们后续需要的列。

    参数：
        path: 输入 CSV 文件路径，例如 "data/pilot_input.csv"

    返回：
        df: pandas DataFrame，可以理解成一个表格（类似 Excel）

    为什么要检查列名？
        因为后面的解析和评分逻辑依赖固定字段。
        如果列名不对，程序应该尽早报错，而不是后面莫名其妙出问题。
    """
    # 用 pandas 读取 CSV 文件
    df = pd.read_csv(path)

    # required_cols = “必须存在的列”
    # 如果这些列缺失，说明输入文件格式和我们预期不一致
    required_cols = [
        "item_id",       # 题目唯一编号，相当于每道题的身份证
        "dataset",       # 题目来自哪个数据集，例如 mmlu / arc / hellaswag
        "subject",       # 更细的学科/主题，例如 formal_logic
        "split",         # 数据集划分，例如 train / validation / test
        "question",      # 题干
        "choice_labels", # 选项标签，通常是 ['A','B','C','D']
        "choices",       # 选项内容，例如 A 对应什么，B 对应什么
        "answer",        # 标准答案（官方正确答案），后面会改名成 gold_label
        "model_id",      # 哪个模型给出的回答，例如 gpt-4o-mini
        "raw_response",  # 模型原始输出文本，这是 Parser 要处理的核心对象
    ]

    # missing = 缺失的列名列表
    # 这里逐个检查 required_cols 中的每一列是否存在于 df.columns 里
    missing = [c for c in required_cols if c not in df.columns]

    # 如果有缺失列，直接报错并告诉你缺了哪些列
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    return df


# =========================================================
# 2. 文本清洗 / 标准化
# =========================================================
def normalize_text(text) -> str:
    """
    作用：
        对模型输出文本做基础清洗，方便后面的正则匹配。

    参数：
        text: 模型原始输出 raw_response

    返回：
        清洗后的字符串

    为什么需要这一步？
        因为模型输出可能有：
        - 空值
        - 首尾空格
        - 花体引号
        - Windows / Unix 不同换行符
        先统一一下格式，后面更容易解析。
    """

    # pd.isna(text) 用来判断是不是缺失值（NaN）
    # 如果是空值，就返回空字符串，避免后面报错
    if pd.isna(text):
        return ""

    # 强制转成字符串，并去掉首尾空白字符
    text = str(text).strip()

    # 把一些花体引号替换成普通引号，减少匹配时的格式干扰
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')

    # 统一换行符
    # Windows 常见 \r\n，老系统可能有 \r，统一成 \n
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    return text


# =========================================================
# 3. 核心函数：从模型回答中提取答案
# =========================================================
def extract_answer(raw_response: str):
    """
    作用：
        从模型原始输出 raw_response 中提取模型最终选择的选项（A/B/C/D）。

    参数：
        raw_response: 模型原始输出文本，例如：
            "[A] The correct translation is ..."
            "The correct answer is B."
            "I choose C."
            "[CD] ..."

    返回：
        pred_label, parse_status, parse_rule

        其中：
        - pred_label:
            解析出的模型答案，应该是 'A' / 'B' / 'C' / 'D'
            如果没法确定，就返回 None

        - parse_status:
            解析状态，取值有三种：
            1) "parsed"
               成功解析出唯一答案
            2) "ambiguous"
               出现多个候选答案，无法确定到底选哪个
            3) "unparsed"
               完全没解析出合法答案

        - parse_rule:
            记录“是通过哪条规则解析出来的”
            这有助于后面 debug：如果发现解析错了，可以追踪是哪条规则导致的。
    """

    # 先对原始文本做清洗
    text = normalize_text(raw_response)

    # 如果清洗后是空字符串，说明没有有效内容
    if not text:
        return None, "unparsed", "empty_text"

    # 把文本转成大写，后面匹配时就不用同时考虑大小写
    # 例如 "The correct answer is b" -> "THE CORRECT ANSWER IS B"
    t = text.upper()

    # -------------------------------------------------
    # Rule 1: 优先看开头的方括号，例如 [A], [B], [CD], [None of the above]
    # -------------------------------------------------
    # re.match(...) 表示“从字符串开头开始匹配”
    # 这个正则的意思是：
    #   如果一开始出现 [ ... ]，就把中括号里的内容抓出来
    m = re.match(r"^\s*\[([^\]]+)\]", t)

    if m:
        # content = 中括号里的内容，例如：
        # [A] -> "A"
        # [CD] -> "CD"
        # [None of the above] -> "NONE OF THE ABOVE"
        content = m.group(1).strip()

        # 情况 1：中括号里只有一个合法选项，例如 [A]
        if re.fullmatch(r"[ABCD]", content):
            return content, "parsed", "leading_bracket_single"

        # 情况 2：中括号里有多个字母，例如 [CD], [BC], [AA]
        if re.fullmatch(r"[ABCD]{2,}", content):
            # dict.fromkeys(content) 是一个常见小技巧：
            # “去重但保留顺序”
            # 例如：
            #   "AA" -> "A"
            #   "CD" -> "CD"
            unique_letters = "".join(dict.fromkeys(content))

            # 如果去重后只剩一个字母，例如 [AA]
            # 可以视为还是一个答案
            if len(unique_letters) == 1:
                return unique_letters, "parsed", "leading_bracket_repeated"

            # 如果去重后仍然有多个不同字母，例如 [CD]
            # 说明模型给了多个候选答案，不能硬判
            return None, "ambiguous", "leading_bracket_multi"

        # 情况 3：中括号里不是合法选项，例如 [None of the above]
        return None, "unparsed", "leading_bracket_non_option"

    # -------------------------------------------------
    # Rule 2: 明确措辞模式
    # 例如：
    #   "Final answer: B"
    #   "The correct answer is C"
    #   "I choose D"
    # -------------------------------------------------
    # high_priority_patterns = 高优先级规则列表
    # 每条规则是一个二元组：
    #   (正则表达式, 规则名字)
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

    # 一条规则一条规则试
    for pattern, rule_name in high_priority_patterns:
        # re.search(...) 表示“在整段文本里查找”
        m = re.search(pattern, t)
        if m:
            # m.group(1) 是正则中 ([ABCD]) 抓到的那个字母
            return m.group(1), "parsed", rule_name

    # -------------------------------------------------
    # Rule 3: 整段文本几乎只有一个选项
    # 例如：
    #   "A"
    #   "(B)"
    #   "C."
    # -------------------------------------------------
    compact = t.strip()

    # re.fullmatch(...) 表示“整段文本必须完全符合这个模式”
    if re.fullmatch(r"\(?[ABCD]\)?[\.]?", compact):
        m = re.search(r"([ABCD])", compact)
        if m:
            return m.group(1), "parsed", "compact_single_letter"

    # -------------------------------------------------
    # Rule 4: 兜底规则
    # 在整段文本中寻找独立出现的 A/B/C/D
    # -------------------------------------------------
    # \b 表示单词边界，作用是避免匹配到普通单词里的字母
    # 比如 "AND" 里的 A、"Because" 里的 B 都不应该被当成答案
    candidates = re.findall(r"\b([ABCD])\b", t)

    # seen 用来“去重但保留顺序”
    # 例如 candidates = ['A', 'A', 'C'] -> seen = ['A', 'C']
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)

    # 如果最后只剩一个候选字母，就视为成功解析
    if len(seen) == 1:
        return seen[0], "parsed", "fallback_single_letter"

    # 如果有多个不同候选字母，说明有歧义
    elif len(seen) > 1:
        return None, "ambiguous", "fallback_multiple_letters"

    # 一个都没有找到，说明没解析出来
    else:
        return None, "unparsed", "no_valid_option_found"


# =========================================================
# 4. 评分函数
# =========================================================
def score_prediction(pred_label, gold_label) -> int:
    """
    作用：
        把“模型预测答案”和“标准答案”比较，输出 0/1 分数。

    参数：
        pred_label: 模型预测答案（你从 raw_response 中提取出来的）
                    例如 'A' / 'B' / 'C' / 'D' / None
        gold_label: 标准答案（官方正确答案）
                    例如 'A' / 'B' / 'C' / 'D'

    返回：
        1 = 预测正确
        0 = 预测错误或无法解析

    注意：
        这里是最简单的二值评分：
        - 答对就 1
        - 答错 / 没解析出来就 0
    """

    # 如果 pred_label 是 None，表示没解析出明确答案
    # 这种情况下直接记 0 分
    if pred_label is None or pd.isna(gold_label):
        return 0

    # 统一转大写后比较，避免大小写带来的误差
    # str(...).upper() 例如 "b" -> "B"
    return int(str(pred_label).upper() == str(gold_label).upper())


# =========================================================
# 5. 主流程：把前面所有步骤串起来
# =========================================================
def main():
    """
    main() = 主程序入口

    它负责把整个流程串起来：
        1. 找到输入文件
        2. 读取 CSV
        3. 把 answer 改名成 gold_label
        4. 对每条 raw_response 运行 extract_answer()
        5. 根据 pred_label 和 gold_label 计算 score
        6. 导出结果文件
        7. 打印摘要信息
    """

    # input_path = 输入文件路径
    # 这里默认你的输入文件放在 data/pilot_input.csv
    # 如果你的文件名不一样，要改这里
    input_path = Path("data/pilot_input.csv")

    # 检查文件是否存在
    if not input_path.exists():
        raise FileNotFoundError(
            f"Cannot find input file: {input_path}\n"
            f"请把你的 CSV 放到这个路径，或者改这里的 input_path。"
        )

    # 读取输入表
    df = load_input_csv(str(input_path))

    # -------------------------------------------------
    # 把 answer 改名成 gold_label
    # -------------------------------------------------
    # answer = 标准答案
    # gold_label 这个名字更清楚，常用于机器学习/评测场景
    df = df.rename(columns={"answer": "gold_label"}).copy()

    # -------------------------------------------------
    # 对每条 raw_response 执行解析
    # -------------------------------------------------
    # parsed_results 的每一行都会是一个三元组：
    #   (pred_label, parse_status, parse_rule)
    parsed_results = df["raw_response"].apply(extract_answer)

    # pred_label = 你从模型原始输出中提取出来的答案
    # 例如 'A' / 'B' / 'C' / 'D'
    # 如果无法确定，就会是 None
    df["pred_label"] = parsed_results.apply(lambda x: x[0])

    # parse_status = 解析状态
    # 取值：
    #   parsed     -> 成功解析
    #   ambiguous  -> 有多个候选，无法确定
    #   unparsed   -> 完全没解析出来
    df["parse_status"] = parsed_results.apply(lambda x: x[1])

    # parse_rule = 哪条规则提取出来的
    # 这个字段对 debug 很有帮助
    df["parse_rule"] = parsed_results.apply(lambda x: x[2])

    # -------------------------------------------------
    # 计算分数 score
    # -------------------------------------------------
    # df.apply(..., axis=1) 表示“按行处理”
    # 也就是对每一行都取出 pred_label 和 gold_label 比较一次
    df["score"] = df.apply(
        lambda row: score_prediction(row["pred_label"], row["gold_label"]),
        axis=1,
    )

    # -------------------------------------------------
    # 调整输出列顺序
    # -------------------------------------------------
    # preferred_cols = 希望输出时优先放在前面的列
    # 这样导出的 CSV 更好读
    preferred_cols = [
        "item_id",       # 题目编号
        "dataset",       # 数据集
        "subject",       # 科目/主题
        "split",         # 数据划分
        "model_id",      # 模型名称
        "gold_label",    # 标准答案
        "raw_response",  # 模型原始回答
        "pred_label",    # 解析出的模型答案
        "score",         # 0/1 分数
        "parse_status",  # 解析状态
        "parse_rule",    # 使用的解析规则
        "question",      # 题干
        "choice_labels", # 选项标签
        "choices",       # 选项文本
    ]

    # out_cols = 实际输出列顺序
    # 先放 preferred_cols，再把其余没列进去的列接到后面
    out_cols = [c for c in preferred_cols if c in df.columns] + [
        c for c in df.columns if c not in preferred_cols
    ]

    scored_df = df[out_cols].copy()

    # -------------------------------------------------
    # 输出目录和输出文件路径
    # -------------------------------------------------
    output_dir = Path("data")

    # mkdir(parents=True, exist_ok=True)：
    # 如果 data 文件夹不存在，就自动创建
    output_dir.mkdir(parents=True, exist_ok=True)

    scored_path = output_dir / "scored_results.csv"
    errors_path = output_dir / "parse_errors.csv"
    summary_path = output_dir / "parse_summary_by_model.csv"

    # -------------------------------------------------
    # 保存主结果表
    # -------------------------------------------------
    # scored_results.csv = 后面统计分析最主要会用到的文件
    scored_df.to_csv(scored_path, index=False, encoding="utf-8-sig")

    # -------------------------------------------------
    # 保存解析失败 / 歧义样本
    # -------------------------------------------------
    # parse_status != "parsed" 的记录都挑出来
    # 这些是后面需要人工检查的重点样本
    error_df = scored_df[scored_df["parse_status"] != "parsed"].copy()
    error_df.to_csv(errors_path, index=False, encoding="utf-8-sig")

    # -------------------------------------------------
    # 保存每个模型的解析情况汇总
    # -------------------------------------------------
    # groupby(["model_id", "parse_status"])：
    #   按 模型 + 解析状态 分组
    # size()：
    #   统计每组有多少条
    # reset_index(name="n")：
    #   把结果整理成普通表格，并把计数列命名为 n
    summary_df = (
        scored_df.groupby(["model_id", "parse_status"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["model_id", "parse_status"])
    )
    summary_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    # -------------------------------------------------
    # 在终端打印摘要，方便你快速检查
    # -------------------------------------------------
    print(f"Saved: {scored_path}")
    print(f"Saved: {errors_path}")
    print(f"Saved: {summary_path}")
    print()

    print("=== Parse Status Summary ===")
    # value_counts() = 统计每种 parse_status 出现了多少次
    print(scored_df["parse_status"].value_counts(dropna=False))
    print()

    print("=== Accuracy by Model ===")
    # 按 model_id 分组，对 score 求平均
    # 因为 score 是 0/1，所以平均值就是准确率 accuracy
    model_acc = scored_df.groupby("model_id")["score"].mean().sort_values(ascending=False)
    print(model_acc)
    print()

    print("=== Overall Accuracy ===")
    # 所有记录的 score 平均值 = 总体准确率
    print(scored_df["score"].mean())


# =========================================================
# 6. Python 程序入口
# =========================================================
# 这句的意思是：
# 如果你是直接运行这个脚本（python src/03_scorer.py），
# 就执行 main()
if __name__ == "__main__":
    main()