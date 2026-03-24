import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from tqdm import tqdm


BASE_DIR = Path(__file__).resolve().parent 



INPUT_FILE = BASE_DIR.parent / "data" / "01_prompts.jsonl"
OUTPUT_JSONL = BASE_DIR.parent / "data" / "02_raw_responses.jsonl"
OUTPUT_CSV = BASE_DIR.parent / "data" / "02_raw_responses.csv"

MODELS = [
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "qwen/qwen-2.5-7b-instruct",
    "meta-llama/llama-3.1-8b-instruct"
]

API_URL = "https://openrouter.ai/api/v1/chat/completions"
# ===========================================

def setup_env():
    """加载环境变量并验证 API Key"""
    ENV_FILE_PATH = BASE_DIR.parent / "my.env"
    load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 错误：未找到 API Key，请检查 env 文件。")
        exit(1)
    print(f"✅ 环境就绪！API Key 加载成功 (开头: {api_key[:10]}...)")
    return api_key


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_ai_response(api_key, model_id, prompt):
    """核心 API 调用逻辑"""
    headers = {
        "Authorization": f"Bearer {api_key.strip().lower() if api_key.startswith('SK-OR') else api_key.strip()}",
        "Content-Type": "application/json"
    }
    
    # 强制单字母输出的 Prompt 注入
    refined_prompt = (
        f"{prompt.strip()}\n\n"
        f"IMPORTANT: Output ONLY the correct option letter (A, B, C, or D).\n"
        f"Do NOT include brackets, periods, or any explanations.\n"
        f"Just the single letter."
    )
    
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": refined_prompt}],
        "temperature": 0,
        "max_tokens": 150
    }
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")
        
    res_data = response.json()
    message = res_data['choices'][0]['message']
    content = message.get('content') or message.get('reasoning') or ""
    
    # 结果清洗
    final_answer = str(content).strip().replace(".", "").replace("[", "").replace("]", "")
    return final_answer if final_answer else "N/A"

def format_item_to_prompt(item):
    """从 jsonl 行数据中提取 prompt 内容"""
    if "messages" in item and len(item["messages"]) > 0:
        return item["messages"][0]["content"]
    return ""

def check_balance(api_key):
    """检查 OpenRouter 账户额度"""
    url = "https://openrouter.ai/api/v1/key"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, headers=headers)
        data = response.json().get("data", {})
        print(f"\n💰 账户额度: 剩余 {data.get('limit_remaining'):.4f} 刀 / 总额 {data.get('limit')} 刀")
    except:
        print("\n⚠️ 无法获取额度信息")

def main():
    api_key = setup_env()
    
    # 1. 加载任务
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 输入文件 {INPUT_FILE} 不存在！")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_tasks = [json.loads(line) for line in f]
    
    # 这里的截取逻辑可根据需求修改，目前保留原代码的 50 条测试逻辑
    tasks = all_tasks[:50]
    print(f"🚀 开始处理，共 {len(tasks)} 个任务，涉及 {len(MODELS)} 个模型")

    results = []
    
    # 2. 执行循环
    for model_id in MODELS:
        print(f"\n🤖 当前模型: {model_id}")
        
        # 使用 tqdm 显示进度
        pbar = tqdm(tasks, desc=f"Progress ({model_id.split('/')[-1]})")
        
        for item in pbar:
            try:
                current_id = item.get('item_id') or item.get('task_id') or 'Unknown'
                formatted_prompt = format_item_to_prompt(item)
                
                raw_answer = get_ai_response(api_key, model_id, formatted_prompt)
                
                # 整合数据
                output_item = item.copy()
                output_item.update({
                    "model_id": model_id,
                    "raw_response": raw_answer,
                })
                
                results.append(output_item)
                
                # 实时追加保存 JSONL
                with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(output_item, ensure_ascii=False) + "\n")
                
                time.sleep(1) # 频率控制
                
            except RetryError as e:
                real_exc = e.last_attempt.exception() if hasattr(e, 'last_attempt') else "Retry failed"
                print(f"\n❌ Task {current_id} 失败 (重试后) -> {real_exc}")
            except Exception as e:
                print(f"\n❌ Task {current_id} 报错 -> {str(e)}")

    # 3. 统计并导出 CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        print(f"\n✅ 处理完成！")
        print(f"📊 总计抓取响应: {len(results)} 条")
        print(f"💾 CSV 文件已保存至: {OUTPUT_CSV}")
    
    check_balance(api_key)

if __name__ == "__main__":
    main()