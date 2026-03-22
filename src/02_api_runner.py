# %%
import os
import json
import time
import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm.notebook import tqdm
from tenacity import RetryError  

# 加载你的 env 文件
load_dotenv(dotenv_path="../env", override=True)
API_KEY = os.getenv("OPENROUTER_API_KEY")

API_URL = "https://openrouter.ai/api/v1/chat/completions"

if API_KEY:
    print(f"✅ 环境就绪！API Key 加载成功 (开头: {API_KEY[:10]}...)")
else:
    print("❌ 错误：未找到 API Key，请检查 env 文件。")

# %%
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(model_id, prompt):
    if not API_KEY or API_KEY == "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
        raise Exception("❌ API_KEY 未配置！")
    
    # Header logic (Keep your fix for SK-OR prefix)
    headers = {
        "Authorization": f"Bearer {API_KEY.strip().lower() if API_KEY.startswith('SK-OR') else API_KEY.strip()}",
        "Content-Type": "application/json"
    }
    
    # 🔴 STICKER PROMPT: Demanding ONLY the letter
    # 强制要求：只输出选项字母
    refined_prompt = f"""{prompt.strip()}

IMPORTANT: Output ONLY the correct option letter (A, B, C, or D). 
Do NOT include brackets, periods, or any explanations.
Just the single letter."""
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": refined_prompt}],
        "temperature": 0,    # 🔒 Keep at 0 for consistency
        "max_tokens": 5      # 🔒 Minimal tokens to prevent chatting
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        res_data = response.json()
        message = res_data['choices'][0]['message']
        content = message.get('content') or message.get('reasoning') or ""
        
        # 🔴 CLEANING: In case the model still adds a period like "A."
        # 结果清洗：防止模型带点或空格
        final_answer = str(content).strip().replace(".", "").replace("[", "").replace("]", "")
        
        # Return only the first character just in case
        return final_answer[0] if final_answer else "N/A"
        
    except Exception as e:
        raise Exception(f"❌ Error: {str(e)}")

print("✅ Strict Single-Letter function is ready!")

def format_item_to_prompt(item):
    question = item.get("question", "")
    choices = item.get("choices", [])
    labels = item.get("choice_labels", ["A", "B", "C", "D"])
    
    # Combine labels and choices: (A) choice1 (B) choice2 ...
    options_str = " ".join([f"({labels[i]}) {choices[i]}" for i in range(len(choices))])
    
    return f"Question: {question}\nOptions: {options_str}"

# %%
import json
import os
import time
from tqdm.notebook import tqdm
from tenacity import RetryError

# 1. Configuration 
input_file = "../data/01_prompts.jsonl"
output_file = "../data/02_raw_responses.jsonl"
MODELS = [
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "anthropic/claude-3.5-haiku",
    "meta-llama/llama-3.1-8b-instruct"
]

# 2. Load P1 tasks 
tasks = []
if os.path.exists(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = [json.loads(line) for line in f]
    print(f"✅ Loaded {len(tasks)} tasks.")
else:
    print(f"❌ Input file {input_file} not found!")

tasks = tasks[:50]  # For testing, limit to first 10 tasks. Remove or adjust for full run.
# Clear results list to avoid duplicates if rerunning 
results = []

# 3. Execution Loop 
for model_id in MODELS:
    print(f"\n🚀 Processing model: {model_id}")
    
    # Using tqdm for progress tracking / 使用进度条
    for item in tqdm(tasks, desc=f"Model: {model_id.split('/')[-1]}"):
        try:
            # --- STEP A: Format the prompt / 核心逻辑：改写问题 ---
            # Use the item_id if task_id is missing / 兼容不同的 ID 字段名
            current_id = item.get('item_id') or item.get('task_id') or 'Unknown'
            
            # Construct the full prompt string / 动态生成 Prompt
            formatted_prompt = format_item_to_prompt(item)
            
            # --- STEP B: Call API / 核心调用 ---
            # Note: Ensure your get_ai_response returns (answer, usage)
            raw_answer = get_ai_response(model_id, formatted_prompt)
            
            # --- STEP C: Integrate results / 整合输出字段 ---
            output_item = item.copy()
            output_item.update({
                "model_id": model_id,
                "raw_response": raw_answer,
            })
            
            results.append(output_item)
            
            # --- STEP D: Real-time Save / 实时追加保存 ---
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(output_item, ensure_ascii=False) + "\n")
            
            # Rate limiting / 控制频率
            time.sleep(1) 
            
        except RetryError as e:
            # Extract underlying exception from Tenacity / 捕获重试失败后的真实原因
            real_exception = e.last_attempt.exception() if hasattr(e, 'last_attempt') else "Unknown Retry Error"
            print(f"\n❌ Task {current_id} FAILED after retries → Reason: {str(real_exception)}")
        
        except Exception as e:
            # Catch non-retry errors / 捕获其他通用错误
            print(f"\n❌ Task {current_id} FAILED (Non-retry error) → {str(e)}")

print(f"\n✅ All tasks finished! Total responses captured: {len(results)}")

# %%
import pandas as pd
import os

# 确保 output_file 路径正确
output_file = "../data/02_raw_responses.jsonl"

if os.path.exists(output_file):
    # 读取 JSONL 文件
    df = pd.read_json(output_file, lines=True)
    
    # 🔍 动态检测 ID 列名 (兼容 item_id 或 task_id)
    id_col = 'item_id' if 'item_id' in df.columns else 'task_id'
    
    # 检查我们需要的列是否存在，防止 display 报错
    available_cols = [col for col in [id_col, 'model_id', 'raw_response', 'answer'] if col in df.columns]
    
    print(f"📊 结果预览 (共 {len(df)} 条记录):")
    if not df.empty:
        display(df[available_cols].head())
    else:
        print("⚠️ 文件是空的。")
else:
    print(f"📭 暂无结果文件：{output_file}")

# %%
import os
import pandas as pd

# 定义文件路径
output_file = "../data/02_raw_responses.jsonl"
csv_output_file = "../data/02_raw_responses.csv"

if os.path.exists(output_file):
    # 1. 读取 JSONL 文件
    df = pd.read_json(output_file, lines=True)
    
    # 🔍 核心改动：动态识别 ID 列 (兼容 item_id 或 task_id)
    id_col = 'item_id' if 'item_id' in df.columns else 'task_id'
    
    # 定义预览和导出时需要的核心列（如果存在的话）
    core_cols = [id_col, 'model_id', 'raw_response']
    if 'answer' in df.columns: core_cols.append('answer')
    if 'ground_truth' in df.columns: core_cols.append('ground_truth')

    # 2. 结果预览
    print(f"📊 结果预览 (ID列名: {id_col}):")
    try:
        # 只显示存在的列，避免 KeyError
        display_df = df[[c for c in core_cols if c in df.columns]].head()
        display(display_df)
    except NameError:
        print(df[[c for c in core_cols if c in df.columns]].head())
    
    # 3. 导出 CSV (使用 utf-8-sig 确保 Excel 打开中文不乱码)
    # 我们直接导出全量 DataFrame，这样 P3 可以看到所有原始字段
    df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ CSV 文件已生成：{csv_output_file}")
    
    # 4. 数据统计
    total_count = len(df)
    models = df['model_id'].unique().tolist()
    print(f"\n📈 统计：共 {total_count} 条记录，涉及 {len(models)} 个模型")
    print(f"🔍 模型列表：{models}")

else:
    print(f"📭 暂无结果文件：{output_file}，请先运行搬运循环。")

# %%
import requests

api_key = os.getenv("OPENROUTER_API_KEY")
url = "https://openrouter.ai/api/v1/key"

headers = {
    "Authorization": f"Bearer {api_key}"
}

response = requests.get(url, headers=headers)
data = response.json().get("data", {})

print(f"总额度限制: {data.get('limit')} 刀")
print(f"剩余可用额度: {data.get('limit_remaining')} 刀")
print(f"已使用额度: {data.get('usage')} 刀")


