from pathlib import Path

# ── Ollama 模型設定 ───────────────────────────────
# 主要對話模型，負責工具呼叫與推理
MODEL        = "qwen3:8b"
# 視覺分析專用模型，qwen3:8b 無法看圖，需要獨立的多模態模型
VISION_MODEL = "llava:7b"
# Ollama 本機 API 端點
OLLAMA_URL   = "http://localhost:11434/api/chat"
# Context window 大小（輸入+輸出共用）。qwen3:8b 原生支援 32768，
# 若不設定 Ollama 會用預設值（通常遠小於此），導致 RECENT_TURNS/RAG_TOP_K
# 塞進去的內容被悄悄截斷
NUM_CTX      = 32768

# ── 驗證模式 ──────────────────────────────────────
# 開啟後 agent_loop 拿到答案後再呼叫一次模型做自我核查
# 預設 False（可由前端 per-request 覆蓋，此為 server-side 預設值）
VERIFY_ANSWER = False

# ── Session 設定 ──────────────────────────────────
# session 對話紀錄的儲存目錄，不存在時自動建立
SESSIONS_DIR  = Path(__file__).parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)
# 每次送給模型的最近幾輪對話（太多會佔用 context window）
RECENT_TURNS  = 10
# RAG 語意搜尋最多回傳幾筆過去對話供參考
RAG_TOP_K     = 10

# ── 系統提示 ──────────────────────────────────────
# 設計原則：只寫模型「不會自發做到」的規則，已由程式碼處理的邏輯不寫進來
# 規則越少，每條規則獲得的注意力越高；過多規則會造成注意力稀釋，反而變笨
SYSTEM_PROMPT = """你是 ZuZu，一個繁體中文的本地 AI 助理。

工具使用規則：
- 任何需要用到日期或時間 → 一定先呼叫 get_current_time，不可自行猜測或使用訓練資料的日期
- 涉及即時資訊、新聞、價格、近期事件 → 一定用 search_web
- 目標網站有 RSS/Atom feed → 優先用 fetch_rss，比 browse_url 快且不觸發反爬蟲
- 拿到列表頁想知道裡面有哪些文章連結 → 用 extract_links
- 需要讀取文章完整內容 → 用 browse_url，但同一網域單次對話最多讀 5 篇
- 需要讀取、建立、修改本機文字檔 → 用 read_file / write_file / append_file
- 需要讀取 PDF → 短文件用 read_pdf，長文件用 read_pdf_page 分批讀取，要切割用 split_pdf
- 需要分析圖片 → 用 analyze_image，可加上具體問題讓回答更精準
- 不確定資料夾內有什麼 → 先用 list_files 查看
- 被問到新聞、資訊、事件時，必須實際用 browse_url 讀取文章內容，不可只憑搜尋摘要或訓練知識回答
- 讀完文章後統整真正發生了什麼事，並給出自己的觀點與判斷，不只是列出資料來源
- 爬到資訊後標註來源可信度（高/中/低）與理由，低可信度內容標記「需查證」
- 同一事件若只有單一來源，主動補搜第二個來源確認
- 一般知識問答可直接回答，不需要每次都搜尋
- 所有檔案操作只限 F:\\python_project\\ai_agent 目錄範圍內，路徑要完整正確，不可自行修改使用者給的路徑
- 爬取的資料若無指定路徑，預設存到 F:\\python_project\\ai_agent\\data\\ 目錄下
- 回答一律使用繁體中文"""
