import json
import requests
from config import MODEL, OLLAMA_URL, RECENT_TURNS, RAG_TOP_K, SYSTEM_PROMPT, VERIFY_ANSWER, NUM_CTX
from tools import TOOLS, run_tool
from tools.web import reset_browse_counts
from tools.vision import analyze_image_b64
import rag


def build_messages(history: list, query: str, image_b64: str = None) -> list:
    # 組合送給模型的完整訊息列表：
    #   1. system prompt（角色定義與規則）
    #   2. RAG 過去相關對話（語意搜尋找出相關紀錄，但排除已在 recent 中的）
    #   3. 最近 N 輪對話（提供短期記憶）
    #   4. 本次使用者提問（可附帶圖片描述）
    recent = history[-(RECENT_TURNS * 2):]
    recent_texts = {m["content"] for m in recent}

    # 從 ChromaDB 語意搜尋過去對話，過濾掉已在 recent 中的重複內容
    retrieved = rag.retrieve(query, top_k=RAG_TOP_K)
    relevant = [
        f"Q: {t['user']}\nA: {t['assistant']}"
        for t in retrieved
        if t["user"] not in recent_texts
    ]

    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    if relevant:
        # 將 RAG 結果以獨立 system 訊息注入，不污染對話流
        msgs.append({
            "role": "system",
            "content": "以下是過去相關的對話紀錄，供你參考：\n\n" + "\n\n---\n\n".join(relevant),
        })
    msgs.extend(recent)

    # 有圖片時：先用 llava 將圖片轉成文字描述，再帶入給 qwen3 一起理解
    # qwen3:8b 沒有原生視覺能力，這是雙模型協作的橋接方式
    if image_b64:
        description = analyze_image_b64(image_b64, query or "請詳細描述這張圖片的內容")
        msgs.append({
            "role": "user",
            "content": f"[圖片分析結果]\n{description}\n\n使用者問題：{query}" if query else f"[圖片分析結果]\n{description}",
        })
    else:
        msgs.append({"role": "user", "content": query})

    return msgs


def _verify_answer(messages: list, answer: str, think: bool) -> str:
    # 把第一次的答案再丟回模型做自我核查（不帶工具，純推理）
    # 讓模型確認數字、邏輯、日期是否正確，有錯就更正，沒錯回原文
    verify_messages = messages + [
        {"role": "assistant", "content": answer},
        {
            "role": "user",
            "content": (
                "請重新確認以上回答是否正確。"
                "重點檢查：數字計算、日期合理性、邏輯推導、工具資料引用。"
                "若有錯誤，直接給出更正後的完整答案；"
                "若答案正確，直接回覆原答案，不需要說「我確認了」或重複解釋。"
            ),
        },
    ]
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": verify_messages, "stream": False, "think": think, "options": {"num_ctx": NUM_CTX}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def agent_loop(messages: list, think: bool, verify: bool = False) -> str:
    # 每次新對話重設 browse 計數器，讓新對話有完整的 5 次配額
    reset_browse_counts()

    # 持續呼叫 Ollama 直到模型不再要求工具，才回傳最終回答
    # 迴圈流程：
    #   模型回應 → 有 tool_calls → 執行工具 → 把結果加入訊息 → 再呼叫模型
    #   模型回應 → 無 tool_calls → 視 verify 決定是否再做一次自我核查，然後回傳
    while True:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "messages": messages, "tools": TOOLS, "stream": False, "think": think, "options": {"num_ctx": NUM_CTX}},
            timeout=120,
        )
        resp.raise_for_status()
        msg = resp.json()["message"]
        messages.append(msg)  # 把模型回應加入訊息串，維持對話上下文

        # 模型沒有要求工具 → 這是最終回答
        if not msg.get("tool_calls"):
            answer = msg["content"]
            # verify=True 時多一次自我核查，會多 3-8 秒但能抓到推理錯誤
            if verify or VERIFY_ANSWER:
                answer = _verify_answer(messages, answer, think)
            return answer

        # 執行模型要求的每個工具，將結果以 role="tool" 訊息回傳給模型
        for tc in msg["tool_calls"]:
            name = tc["function"]["name"]
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)  # Ollama 有時回傳 JSON 字串而非 dict
            messages.append({"role": "tool", "content": run_tool(name, args)})
