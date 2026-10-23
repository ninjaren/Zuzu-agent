# LLM / Harness / MCP 教學筆記

這份筆記整理「LLM 大腦」「Harness」「MCP」三者的關係，並對照本專案（qwen3_8b + Ollama）的實際程式碼說明。

---

## 1. LLM 本身是什麼？

LLM（大型語言模型，像 qwen3_8b）可以想成一個**關在罐子裡的聰明大腦**：

- 它只會做一件事：**輸入文字（數字 token）→ 輸出文字（數字 token）**
- 它**沒有手、沒有腳、沒有眼睛**：不能自己讀檔案、不能自己上網、不能自己執行程式
- 它**沒有記憶力**：每次對話都要有人把「之前聊過的內容」重新告訴它，它自己不會記得

所有「聰明的行為」（讀檔案、呼叫工具、查資料）其實都不是大腦自己做的，而是外層的程式幫它做、再把結果餵回去給它看。

---

## 2. Harness 是什麼？

**Harness**（原意是「馬具」）= 包裹、驅動 LLM 的那層程式碼，負責幫大腦裝上「手腳眼睛」。

Harness 負責：

- 🧰 **管理工具**：準備好各種工具（讀檔案、搜尋網頁、算數學……），大腦要用哪個就遞給它
- 🔁 **跑迴圈**：大腦說要用工具 → harness 真的去執行 → 把結果回報給大腦 → 大腦再想下一步，直到任務完成
- 📋 **管理對話狀態**：記住對話歷史、上下文，每次打電話給大腦都重新整包送過去
- 🚦 **安全把關**：危險操作（刪檔案、花錢）會先問使用者，不會讓大腦自己亂做
- 🖥️ **呈現結果**：把大腦的話顯示在畫面上

> 一句話：**LLM 大腦 = 只會「想」和「說」；Harness = 幫大腦把「說」變成「真的去做」的身體。**

### 本專案的 Harness 在哪裡？

本專案的 harness 就是 [`app.py`](../app.py) + [`agent_runner.py`](../agent_runner.py)：

- `app.py`：Flask 伺服器，接收使用者請求，管理 session
- `agent_runner.py` 的 `agent_loop()`：真正的迴圈引擎——打電話給 Ollama（qwen3:8b）、判斷有沒有工具呼叫、執行工具、把結果餵回去，直到模型給出最終答案

---

## 3. LLM 和 Harness 中間是什麼？

大腦和身體不是直接黏在一起的，中間有三層東西：

```
LLM 大腦（只認得數字 token）
   ⬆️⬇️ API（打電話：把對話內容整包傳過去，收回應）
   ⬆️⬇️ Tokenizer（文字 ⇄ 數字 互轉的翻譯機）
   ⬆️⬇️ 工具呼叫格式解讀（大腦吐出特殊格式文字，harness 判斷是「說話」還是「要用工具」）
Harness（身體）
```

- **API**：每次對話都要把系統提示詞、歷史紀錄、可用工具清單整包送過去，因為大腦沒記憶
- **Tokenizer**：大腦只認得數字（token），文字要先轉成數字送進去，大腦吐出的數字也要轉回文字
- **工具呼叫格式**：大腦其實不會真的「按按鈕」呼叫工具，它只是吐出一段符合特定格式的文字（例如 `tool_calls`），harness 自己判斷「這是要呼叫工具」，然後真正去執行

本專案對應程式碼：[`agent_runner.py:83-106`](../agent_runner.py) 的 `requests.post(OLLAMA_URL, ...)` 就是那通「電話」，`msg.get("tool_calls")` 就是判斷大腦是不是要呼叫工具。

---

## 4. Harness 是雙向溝通

Harness 不只是「執行命令」，它是**來回不斷傳遞資訊**的迴圈：

```
方向一：Harness → LLM
  傳：系統提示詞、對話歷史、可用工具清單、工具執行後的結果

方向二：LLM → Harness
  傳：要給使用者看的文字，或「我要用某個工具」的請求
```

一輪一輪來回，直到大腦不再要求用工具，harness 才把最終答案顯示給使用者。

---

## 5. 自我檢查機制（Self-Verification）

有兩種常見做法，差別在「有幾個大腦、有幾個 harness」：

### 單一 Harness 自我核查（本專案採用）

**沒有第二個大腦，也沒有第二個 harness**，只是同一個 harness 把同一顆大腦問了**兩次**，第二次換了「檢查員」的提問角度。

本專案實作：[`agent_runner.py:50-71`](../agent_runner.py) 的 `_verify_answer()`：

```python
def _verify_answer(messages, answer, think):
    verify_messages = messages + [
        {"role": "assistant", "content": answer},                 # 把第一次答案塞回去
        {"role": "user", "content": "請重新確認以上回答是否正確..."},  # 換個角度問
    ]
    resp = requests.post(OLLAMA_URL, json={"model": MODEL, ...})  # 還是同一個 model
    return resp.json()["message"]["content"]
```

觸發方式：
- [`config.py`](../config.py) 的 `VERIFY_ANSWER`（全域預設，目前 `False`）
- `app.py` 的 `/chat` 端點可傳 `verify: true` 做 per-request 覆蓋

> 目前是「問一次檢查員」，不是「重複 5 次取多數決」的 self-consistency。保持現狀，先不動。

### Multi-agent：多個獨立 Harness 互相傳訊息

**真的有多個獨立運作的 harness**，各配一顆大腦（可能同一模型開多實例，也可能不同模型），彼此透過訊息互相溝通，例如「一個負責寫程式、一個負責審查、一個負責統籌」。

這種架構成本更高，但適合需要分工的複雜任務。目前本專案**沒有**採用這種架構。

| | 自己跟自己檢查 | Multi-agent |
|---|---|---|
| 大腦數量 | 1 個（重複使用） | 可能多個獨立的 |
| Harness 數量 | 1 個 | 2 個以上 |
| 溝通方式 | 同一 harness 內部換提示詞重打電話 | 不同 harness 之間互傳訊息 |
| 成本 | 較低 | 較高 |

---

## 6. MCP 是什麼？

**MCP（Model Context Protocol）= AI 工具界的「統一插頭規格」**。

以前每個工具（連資料庫、連瀏覽器、連 Email）都要工程師自己寫一套專屬連接方式，無法共用。有了 MCP，只要工具做成「MCP 插頭」形狀，任何支援 MCP 的系統都能直接插上去用。

### Harness 跟 MCP 差在哪？

| | Harness | MCP |
|---|---|---|
| 是什麼 | 整個「身體系統」，決定何時用工具、要不要先問使用者 | 一種「連接規格」，像插頭/接頭 |
| 比喻 | 你整個人（手腳腦袋怎麼協調） | USB 線的接頭形狀 |

Harness 是老闆，決定什麼時候用工具；MCP 只是讓 harness 能輕鬆接上各種外部服務的標準插座。

---

## 7. Harness 和 MCP 中間是什麼？

```
Harness（身體）
   ⬇️ MCP Client（內建的「插座轉接器」，知道怎麼講 MCP 語言）
   ⬇️ Transport（傳輸線：stdio 本機管道，或 HTTP/SSE 網路連線）
   ⬇️ JSON-RPC（講話規則：tools/list 問有什麼工具、tools/call 呼叫工具）
MCP Server（實際提供工具的程式）
```

1. **MCP Client**：Harness 要先內建一段程式，學會「MCP 這門語言」
2. **Transport**：實體傳輸線——同機用 stdio（管道），跨機用網路（HTTP/SSE）
3. **JSON-RPC**：雙方講話的格式規則，例如：
   ```json
   Harness 問：「你有哪些工具？」(tools/list)
   MCP Server 答：「read_file、write_file、search_web...」
   Harness 說：「呼叫 read_file，參數 xxx.txt」(tools/call)
   MCP Server 答：「檔案內容是：......」
   ```

---

## 8. 整條鏈串起來

```
LLM 大腦
  ⇄ API + Tokenizer（打電話 + 文字數字互轉）
  ⇄ Harness（身體：管工具、跑迴圈、把關安全）
  ⇄ MCP Client + Transport + JSON-RPC（插座轉接器 + 傳輸線 + 講話規則）
  ⇄ MCP Server
  ⇄ 真正的工具／資料（檔案、資料庫、瀏覽器……）
```

---

## 9. 專案現況備註（2026-10-16）

- 目前接的是 **qwen3_8b**（透過 Ollama 本機 API，`http://localhost:11434/api/chat`），原因是目前電腦硬體只跑得起這個規模的模型
- 介面是開放的（標準 Ollama chat API 格式），未來硬體升級後可直接換成更大的模型，不需要重寫 harness 邏輯
- 自我檢查機制維持現狀（單次驗證，非 multi-agent），暫不升級
- 目前**尚未接 MCP**；若未來要讓 qwen3_8b 的 harness 也能用標準化的 MCP 工具生態，需要額外實作 MCP Client + Transport + JSON-RPC 這三層
