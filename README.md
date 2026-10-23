# ZuZu — 本機 AI 助理

基於 [Ollama](https://ollama.com/) + qwen3:8b 的本機 AI 代理人，透過 Flask 提供網頁介面。支援 29 種工具呼叫、多 session 管理、RAG 語意記憶、圖片分析。

---

## 功能概覽

| 功能 | 說明 |
|------|------|
| 網路搜尋 | DuckDuckGo 搜尋，不需 API Key |
| 網頁爬蟲 | 靜態 HTTP 爬取，自動偵測 JS 動態渲染頁面並提示改用搜尋 |
| RSS 訂閱 | 解析 RSS 2.0 / Atom feed，比爬蟲更快更穩 |
| 連結提取 | 從列表頁抓出所有超連結，供進一步選擇閱讀 |
| 天氣查詢 | wttr.in 免費 API，支援中文城市名、英文、機場代碼，含逐時預報 |
| 股票報價 | 台灣上市走證交所官方 API，美股走 Yahoo Finance，支援一次查多支 |
| 大盤指數 | TWSE OpenAPI 台灣加權指數等主要指數 |
| 虛擬貨幣 | CoinGecko 免費 API，BTC/ETH/SOL 等，含 24h 漲跌幅與市值 |
| 匯率查詢 | open.er-api.com 免費端點，支援 USD/TWD/JPY/EUR 等主要貨幣 |
| 計算機 | AST 白名單安全求值，支援四則、次方、sqrt/sin/log 等函式與 pi/e 常數 |
| 股票圖表 | 繪製收盤折線 + MA5/MA20 + 成交量 PNG 圖，存於 data/charts/ |
| 本機檔案 | 讀取、寫入、附加、刪除、搬移文字檔，限制在指定目錄內 |
| CSV 讀取 | 自動偵測分隔符與編碼（UTF-8/Big5/CP950），適合券商對帳單 |
| PDF 處理 | 全文讀取、分頁讀取、頁面切割另存 |
| 圖片分析 | 透過 llava:7b 視覺模型分析圖片（拖拉上傳或本機路徑） |
| 剪貼簿 | 讀取系統剪貼簿文字，讓使用者直接貼文字進對話 |
| QR Code | 將文字或網址產生成 PNG，存於 data/qrcodes/ |
| IP 查詢 | 查詢任意 IP 的地理位置、ISP、時區，不填則查本機對外 IP |
| GitHub 週報 | 抓取 GitHub 本週熱門 10 大專案，翻譯成繁體中文存成週報 .md；自動標記 🆕 首次上榜 / 🔁 連續上榜 N 週 |
| 多 session | 每個對話獨立儲存，可自由切換、重新命名、刪除 |
| RAG 記憶 | ChromaDB 向量搜尋，讓模型能回憶過去相關對話 |
| Think 模式 | 開啟 qwen3 的延伸思考，推理更嚴謹（速度較慢） |

---

## 系統需求

- Python 3.11+
- [Ollama](https://ollama.com/) 已安裝並在背景執行

### 需要的 Ollama 模型

```bash
ollama pull qwen3:8b          # 主要對話模型
ollama pull llava:7b          # 圖片分析（可選，不用則無法分析圖片）
ollama pull nomic-embed-text  # RAG 語意嵌入（可選，不用則關閉 RAG）
```

---

## 安裝與啟動

### 必要套件

```bash
pip install flask requests ddgs pypdf chromadb matplotlib
```

### 選用套件（對應特定工具）

```bash
pip install pyperclip       # 剪貼簿工具
pip install qrcode[pil]     # QR Code 產生工具
```

> 未安裝選用套件時工具仍可正常執行，呼叫時會回傳安裝提示而不是崩潰。

### 啟動

```bash
cd F:\python_project\ai_agent\qwen3_4b
python app.py
```

瀏覽器開啟 `http://127.0.0.1:5000`

---

## 目錄結構

```
qwen3_4b/
├── app.py              # Flask 主程式，所有 HTTP 路由
├── agent_runner.py     # 訊息組合 + Ollama 工具呼叫迴圈
├── config.py           # 模型設定、路徑、SYSTEM_PROMPT
├── session_manager.py  # session 對話紀錄的讀寫管理
├── rag.py              # ChromaDB 向量儲存與語意搜尋
├── tools/
│   ├── __init__.py     # 工具匯總（TOOLS 列表、run_tool 派送）
│   ├── system.py       # get_current_time
│   ├── web.py          # search_web / browse_url / fetch_rss / extract_links
│   ├── weather.py      # get_weather（wttr.in）
│   ├── stock.py        # get_stock_price / get_market_index / get_multiple_stocks
│   ├── crypto.py       # get_crypto_price / get_multiple_cryptos / get_exchange_rate
│   ├── calculator.py   # calculate（AST 安全數學求值）
│   ├── chart.py        # plot_stock_chart（matplotlib PNG 走勢圖）
│   ├── github_trending.py  # get_github_trending / generate_weekly_report
│   ├── file_ops.py     # list_files / read_file / write_file / append_file
│   │                   # read_csv / delete_file / move_file
│   ├── pdf_ops.py      # read_pdf / read_pdf_page / split_pdf
│   ├── vision.py       # analyze_image（llava:7b）
│   └── utils.py        # read_clipboard / create_qr_code / get_ip_info
├── templates/
│   └── index.html      # 前端 UI（純 HTML + JS，無框架依賴）
├── sessions/           # session 對話紀錄（JSON，自動產生）
├── data/
│   ├── charts/         # 股票走勢圖 PNG（自動產生）
│   ├── qrcodes/        # QR Code PNG（自動產生）
│   └── weekly_github/  # GitHub 週報 .md 與 seen.json（自動產生）
└── chroma_db/          # RAG 向量資料庫（自動產生）
```

---

## 工具詳細說明

### 網路工具（tools/web.py）

**`search_web(query)`**
用 DuckDuckGo 搜尋，回傳最多 5 筆結果（標題、摘要、網址）。

**`browse_url(url)`**
讀取靜態網頁文字內容（最多 5000 字）。
- 速率限制：同一網域單次對話最多 5 次，每次間隔 1 秒
- 黑名單：facebook、instagram、twitter、x.com、linkedin
- **JS 偵測**：自動判斷 JS 動態渲染的空殼頁，回傳錯誤訊息提示改用 `search_web`

**`fetch_rss(url, max_items=10)`**
解析 RSS 2.0 或 Atom feed，速度比爬蟲快，且不觸發反爬蟲。

**`extract_links(url, max_links=20)`**
從網頁抓出所有超連結，適合先看列表頁再選擇性深入閱讀。

---

### 天氣工具（tools/weather.py）

**`get_weather(location)`**
查詢即時天氣、今日溫度範圍、濕度、風速、UV 指數、逐時預報（每 3 小時）、未來兩天預報。
- 使用 wttr.in 免費 API，不需 API Key
- 支援中文城市名（台北）、英文（Taipei）或機場代碼（TPE）

---

### 股票工具（tools/stock.py）

台灣上市股票走 **台灣證交所 OpenAPI**（官方、免費、無需 Key），含中文名稱、本益比、殖利率、股價淨值比。台灣上櫃與美股走 Yahoo Finance。

**`get_stock_price(symbol)`**
查詢單一股票：純數字代碼視為台股上市（如 `2330`），加 `.TWO` 為上櫃（如 `6547.TWO`），英文代碼為美股（如 `AAPL`）。

**`get_market_index()`**
查詢台灣大盤：發行量加權股價指數、未含金融股指數、未含電子股指數、臺灣50指數。

**`get_multiple_stocks(symbols)`**
逗號分隔，一次最多 10 支，台股批次下載一次完整資料再過濾，不重複呼叫 API。

---

### 虛擬貨幣與匯率（tools/crypto.py）

**`get_crypto_price(symbol)`**
查詢單一虛擬貨幣即時報價（美元＋台幣），含 24h 漲跌幅與市值。
使用 CoinGecko 免費 API，不需 Key，支援 BTC/ETH/SOL/DOGE/XRP/ADA 等 25+ 幣種。

**`get_multiple_cryptos(symbols)`**
逗號分隔，一次最多 10 個，批次呼叫 CoinGecko。

**`get_exchange_rate(from_currency, to_currency, amount)`**
查詢即時匯率並換算金額。to_currency 填 `ALL` 可一次看常用貨幣（TWD/USD/EUR/JPY/CNY/HKD/GBP/KRW/SGD/AUD）一覽。

---

### 計算機（tools/calculator.py）

**`calculate(expression)`**
安全計算數學表達式，使用 Python AST 白名單解析，完全不使用 `eval()`。

支援運算子：`+ - * / // % **`

支援函式：`sqrt` `log` `log2` `log10` `exp` `sin` `cos` `tan` `asin` `acos` `atan` `ceil` `floor` `factorial` `abs` `round`

支援常數：`pi` `e` `tau`

---

### 圖表工具（tools/chart.py）

**`plot_stock_chart(symbol, period="3mo")`**
繪製股票價格走勢圖並存為 PNG，回傳圖片絕對路徑。

- **資料來源**：Yahoo Finance 歷史 API（OHLCV），不需安裝 yfinance
- **台股代碼**：純數字自動補 `.TW`（如 `2330` → `2330.TW`）
- **圖表內容**：上方收盤折線 + MA5（橘）+ MA20（紫），下方成交量（漲綠跌紅）
- **period 可選**：`1mo` / `3mo` / `6mo` / `1y` / `2y` / `5y`，預設 `3mo`

---

### 檔案工具（tools/file_ops.py）

所有操作限制在 `F:\python_project\ai_agent` 目錄下，路徑穿越會被擋住。

| 工具 | 說明 |
|------|------|
| `list_files(path)` | 列出資料夾內容 |
| `read_file(path)` | 讀取文字檔全文 |
| `write_file(path, content)` | 建立或覆寫檔案 |
| `append_file(path, content)` | 在末尾附加內容 |
| `read_csv(path, max_rows=50)` | 讀取 CSV，自動偵測分隔符與編碼（UTF-8/Big5/CP950） |
| `delete_file(path)` | 永久刪除檔案（不含目錄） |
| `move_file(src, dst)` | 搬移或重新命名，自動建立目標目錄 |

---

### PDF 工具（tools/pdf_ops.py）

| 工具 | 說明 |
|------|------|
| `read_pdf(path)` | 讀取全文（短文件用） |
| `read_pdf_page(path, start, end)` | 讀取指定頁數範圍（長文件分批用） |
| `split_pdf(path, start, end, output)` | 切割指定頁數另存新檔 |

> 注意：掃描圖片版 PDF 無法提取文字，需要 OCR 工具。

---

### 圖片工具（tools/vision.py）

**`analyze_image(path, question)`**
分析本機圖片，支援 jpg / png / gif / bmp / webp。
內部切換到 `llava:7b` 模型處理，結果以文字回傳給 qwen3 繼續推理。

---

### 雜項工具（tools/utils.py）

**`read_clipboard()`**
讀取系統剪貼簿文字，讓使用者說「幫我分析剛複製的內容」時直接取用，不需重新貼文字。
需要：`pip install pyperclip`

**`create_qr_code(text, filename="")`**
將文字或網址產生成 QR Code PNG 圖片，存至 `data/qrcodes/`，回傳路徑。
需要：`pip install qrcode[pil]`

**`get_ip_info(ip="")`**
查詢 IP 的地理位置（國家、城市）、ISP 業者與時區。不填 ip 則查本機對外公網 IP。

---

### GitHub 週報工具（tools/github_trending.py）

**`get_github_trending(count=10)`**
抓取 [GitHub Trending（週增星數）](https://github.com/trending?since=weekly) 前 N 名，回傳英文原文資料，agent 收到後會翻譯並可存成 .md 週報。

- 上榜標記：🆕 首次上榜 / 🔁 連續上榜 N 週（紀錄在 `data/weekly_github/seen.json`）
- 專案名稱（`owner/repo` 格式）永遠保留英文，只翻譯描述
- 每週以 ISO 週次命名（例如 `2026-W42.md`）

**自動啟動**：Flask 啟動時，背景 thread 會自動偵測本週報告是否存在，若無則完整產生（抓取 + 批次翻譯 + 寫入 .md），不需手動觸發。

---

## 架構說明

```
使用者輸入
    │
    ▼
build_messages()
    ├── system prompt
    ├── RAG 相關過去對話（ChromaDB 語意搜尋）
    ├── 最近 10 輪對話（短期記憶）
    └── 本次問題（有圖片則先 llava 描述）
    │
    ▼
agent_loop()  ←─────────────────────┐
    │                               │
    ▼                               │
Ollama qwen3:8b                     │
    │                               │
    ├── 有 tool_calls → run_tool() ──┘
    └── 無 tool_calls → 回傳最終回答
```

---

## 設定說明（config.py）

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `MODEL` | `qwen3:8b` | 主要對話模型 |
| `VISION_MODEL` | `llava:7b` | 圖片分析模型 |
| `RECENT_TURNS` | `10` | 送給模型的最近幾輪對話 |
| `RAG_TOP_K` | `10` | RAG 語意搜尋最多回傳幾筆 |

### SYSTEM_PROMPT 設計原則

只寫模型「不會自發做到」的規則。已由程式碼處理的邏輯（如 JS 渲染頁面偵測）不寫進 prompt，避免規則過多造成注意力稀釋，反而讓模型變笨。

---

## 開發過程遇到的難題與解法

### 1. JS 動態渲染頁面抓不到內容

**問題**
`browse_url` 用 `requests.get()` 做靜態 HTTP 請求，碰到 Yahoo Finance、鉅亨網等以 JavaScript 載入資料的頁面，只會拿到空的 HTML 骨架，模型收到幾乎是空的回應後直接放棄，或胡亂回答。

**失敗方案**
在 system prompt 加規則：「若 browse_url 取得內容為空，改用 search_web」。問題是規則越加越多，模型注意力被稀釋，整體反而變笨。

**最終解法**
在 `browse_url` 程式碼內加入 `_is_js_rendered()` 偵測：HTML 夠大但提取文字 < 300 字，且含 JS 框架標記（`__NEXT_DATA__`、`data-reactroot` 等）時，直接回傳明確的錯誤字串：
```
[JS渲染頁面] ... 請改用 search_web 搜尋相關新聞或文章。
```
模型收到這個訊息就知道要換策略，不需要靠 prompt 規則。同時移除原本的 system prompt 規則，讓 prompt 保持精簡。

**注意點**
偵測邏輯必須在文字夠少時才觸發，否則有完整 SSR（伺服器端渲染）的 Next.js 新聞站也有 `__NEXT_DATA__`，會被誤判為空殼。

---

### 2. System Prompt 越加越長，模型越來越笨

**問題**
每次遇到模型行為不對就往 system prompt 加規則，規則超過一定數量後，模型的注意力被分散，每條規則都變弱，甚至互相干擾。

**解法**
確立原則：**程式碼能處理的邏輯不寫進 prompt**。
- 行為規則（JS 頁面偵測、速率限制、路徑安全）→ 移進程式碼
- Prompt 只留「模型不會自發做到」的高層行為指引（例如：一定先查時間、標註來源可信度）

---

### 3. 路徑穿越安全漏洞

**問題**
`_safe_path` 用 `str(p).startswith(str(workspace))` 來驗證路徑，但 `F:\python_project\ai_agentXXX` 也會通過檢查，因為它確實以 `ai_agent` 開頭。

**解法**
在比較字串後加上路徑分隔符：
```python
str(p).startswith(str(workspace) + os.sep)
```
這樣 `ai_agentXXX` 就無法通過，只有真正的子路徑才合法。

---

### 4. 模型自行猜測日期（用訓練資料的年份）

**問題**
問模型「今天是幾月幾日」或要求在檔案裡寫入日期，模型會直接用訓練截止日期附近的年份回答，完全不對。

**解法**
建立 `get_current_time` 工具，並在 system prompt 明確規定：任何需要日期或時間的場景一律先呼叫此工具，不可自行猜測。

---

### 5. qwen3:8b 無法分析圖片

**問題**
使用者希望能拖拉圖片到介面上讓模型分析，但 qwen3:8b 是純文字模型，沒有視覺能力。

**解法**
雙模型協作架構：
1. 使用者上傳圖片
2. `agent_runner` 先呼叫 `llava:7b`（多模態模型）將圖片轉成文字描述
3. 再將描述結果帶入給 qwen3:8b 繼續推理回答

代價是需要額外下載 llava:7b（約 4GB），且兩次推理會消耗較多時間與 VRAM。

---

### 6. 台股 API 的民國年格式

**問題**
台灣證交所 OpenAPI 回傳的日期格式為民國年，例如 `"1151014"` 代表民國 115 年 10 月 14 日 = 2026-10-14，直接顯示會讓使用者困惑。

**解法**
加入 `_roc_to_ad()` 轉換函式，取前三位加 1911 換算成西元年：
```python
def _roc_to_ad(roc_str: str) -> str:
    year = int(roc_str[:3]) + 1911
    return f"{year}-{roc_str[3:5]}-{roc_str[5:7]}"
```

---

### 7. 股票漲跌箭頭方向判斷錯誤

**問題**
初版用「收盤價 ≥ 開盤價」來決定顯示 ▲ 或 ▼，但這是當天內的震盪方向，不是相對昨日的漲跌。

**解法**
改用 TWSE API 直接提供的 `Change` 欄位（正數=漲，負數=跌），同時加上 `isdigit()` 保護避免空字串造成 `int()` 崩潰。

---

### 8. 計算機安全求值：為什麼不能用 eval()

**問題**
最直接的做法是 `eval(expression)`，但 `eval()` 會執行任意 Python 程式碼。使用者（或注入攻擊）輸入 `__import__('os').system('del /s *')` 就能執行系統指令。

**解法**
使用 Python `ast` 模組將表達式解析成語法樹，再遞迴求值，只允許白名單內的節點類型（數字常數、二元運算、一元運算、白名單函式呼叫），其他節點一律拒絕：
```python
tree = ast.parse(expression, mode="eval")
result = _eval_node(tree.body)
```

---

### 9. 模型能力上限（8b 參數的天花板）

**問題**
qwen3:8b 在同時需要「工具呼叫 + 深度分析 + 專業判斷」時容易顧此失彼，例如財報分析、複雜多步推理往往結果淺薄。

**結論**
接受這是硬體限制（電腦同時還有交易程式常駐）。調整定位：ZuZu 負責**資料收集與摘要**，使用者自己做最終判斷。在這個定位下 8b 表現穩定。

---

### 10. GitHub Trending 的重複專案如何處理

**問題**
GitHub 上的熱門專案可能連續多週出現（例如某個 AI 框架爆紅後維持 4 週），若每週的報告都完整列出，使用者看到的是重複資訊，無法快速辨認哪些是真正的新面孔。

**失敗方案**
直接過濾掉重複的專案（只顯示未出現過的）。問題是熱度可能持續，直接過濾會讓使用者以為那週「沒什麼新趨勢」，資訊反而不完整。

**解法**
保留全部 10 名，但加入標記：
- 🆕 首次上榜：本週第一次出現
- 🔁 連續上榜 N 週：已累計出現 N 次（第幾次出現一目瞭然）

出現紀錄存在 `data/weekly_github/seen.json`，以 `owner/repo` 為 key，記錄首次週次與全部出現週次列表。

---

### 11. GitHub 週報翻譯策略：批次 vs 逐條

**問題**
每個專案的描述都是英文，需要翻譯成繁體中文才對使用者友善。若對每筆描述單獨呼叫 Ollama 一次，10 個專案需要 10 次 API round-trip，加上每次模型啟動的 overhead，總時間太長。

**解法**
一次呼叫傳入所有 10 條描述（格式：`1. xxx\n2. xxx\n...`），要求模型逐條輸出翻譯，最後解析出 N 個結果。速度快約 5-8 倍。
失敗安全：模型若少回傳幾條，自動用原文補齊；若整個呼叫失敗，全部退回英文原文，不中斷週報寫入。

---

### 12. 週報產生的時機：排程 vs 口令 vs 啟動自動檢查

**三種方案**
| 方案 | 做法 | 缺點 |
|------|------|------|
| Windows 工作排程器 | 每週一定時呼叫腳本 | 需設定排程；ZuZu 不開也會跑 |
| 使用者口令觸發 | 說「查本週熱門」就呼叫工具 | 依賴使用者主動，容易忘記 |
| **啟動自動檢查（採用）** | Flask 啟動時背景 thread 偵測本週 .md 是否存在，不存在就產生 | 需要 Ollama 在背景，首次啟動多約 2 分鐘 |

採用啟動自動檢查方案，符合「工具開著就能用，不需要記得去觸發」的本機助理使用習慣。

---

## 自我驗證機制

### 單次自我核查（已實作）

agent_loop 拿到最終答案後，將答案丟回模型再問一次：

> 「請重新確認以上回答是否正確。重點檢查：數字計算、日期合理性、邏輯推導、工具資料引用。若有錯誤，給出更正後的完整答案；若正確，直接回覆原答案。」

這次呼叫**不帶工具**，模型只能用推理做核查，避免引入新的搜尋結果干擾。

網頁右上角「驗證模式」toggle 可 per-request 控制開關（橘色），預設關閉。
開啟後每次回答會多 3-8 秒，適合數學計算、資料彙整等需要高準確度的場景。

### Self-Consistency 多數投票（未採用）

**原理**：同一問題跑 N 次，取最多人回答的那個當最終答案。

**為何不採用**：

1. **工具結果是確定性的**：ZuZu 的答案大部分來自工具（股票 API、天氣 API、網頁爬蟲），工具每次回傳相同資料，變異只來自模型的最後一段文字推理。跑 3 次只是把同樣的工具呼叫重複 3 遍，浪費資源。
2. **速度代價高**：本機跑 qwen3:8b 一次約 10-30 秒，3 次就是 30-90 秒，使用體驗大幅下降。
3. **適用場景不同**：Self-Consistency 對「純推理、無外部資料」的數學或邏輯題效果最好。ZuZu 以工具驅動為主，適合場景有限。
4. **單次核查已夠**：一次核查能抓到絕大多數的計算和邏輯錯誤，成本只有 Self-Consistency 的三分之一。

若未來新增「純推理計算模式」（不呼叫工具的場景），可考慮對該類問題加入 Self-Consistency（跑 3 次，temperature 0.5-0.8）。

---

## 已知限制

- **JS 渲染頁面**：Yahoo Finance、鉅亨網等股票類網站以 JavaScript 動態載入資料，靜態 GET 拿不到實際內容。偵測到後會自動提示改用 `search_web`。
- **股票資料時效**：TWSE OpenAPI 為當日收盤後更新，非即時報價；美股透過 Yahoo Finance 非官方 API，偶爾受限。
- **虛擬貨幣 API 速率**：CoinGecko 免費層每分鐘約 30 次，連續大量查詢可能觸發 429 錯誤。
- **模型能力上限**：qwen3:8b 適合資料收集與摘要，深度專業分析（財報解讀、複雜推理）建議使用者自行判斷。
- **掃描 PDF**：無法提取文字，需搭配 OCR 工具（未內建）。
- **圖片上傳大小**：受限於瀏覽器記憶體，超大圖片建議先壓縮。
- **GitHub Trending 反爬蟲**：GitHub 頁面偶爾更改 HTML 結構，可能導致解析失敗（回傳 0 筆），此時工具會回傳提示訊息，不會崩潰。
- **週報首次啟動時間**：新一週首次啟動 ZuZu 時，背景 thread 需約 1-3 分鐘完成翻譯，期間可正常使用其他功能。
