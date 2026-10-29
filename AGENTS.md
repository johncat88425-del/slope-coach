# AGENTS.md：實物模擬實驗教練（Slope Coach）

這份檔案是所有 AI 工具共用的專案規則。Muse Code、Codex、Antigravity 會自動讀 `AGENTS.md`；Claude Code 透過 `CLAUDE.md` 匯入本檔。人類負責人是 john。

## 你是誰？先對照這張表（最重要）

這個 repo 有五個 AI 一起工作，每個只做自己的部分：

| 你是 | 你的工作 | 你**不**做 |
| --- | --- | --- |
| Muse Code | `meta_client/`：所有 Meta API 呼叫、代理、語音 | 前端、物理公式、研究文件 |
| Claude Code | `physics/`、`backend/`、審查 PR | 前端樣式、研究文件 |
| Codex | `frontend/`：五個畫面、圖表、匯出 | 後端、研究文件、做遊戲或示範動畫 |
| Antigravity | 開發環境、端到端瀏覽器測試、部署 | 大改架構、研究文件 |
| Manus | 研究與文件（T21–T23） | 任何程式碼 |

**如果 john 給你的任務屬於別人（例如 Codex 收到 T21–T23），先停下來跟 john 確認，不要照做。**

我們要做的是一個**網站工具**：使用者上傳自己拍的真實實驗影片，系統做測量和比較。不是遊戲、不是物理模擬動畫、不是 PhET 那種虛擬實驗。

## Muse 優先（john 10/28 決定）

要得名，評審要看到 Muse 是這個作品的主角。所以：
- **產品裡所有「理解、判斷、說明」都交給 Meta 模型**：Spark 看場景、建議起滑時刻、選下一次驗證、把結果寫成使用者看得懂的話；SAM 追蹤；Voice Transcribe 語音口述。程式（physics）只負責算數字和守住規則。
- **新的開發任務優先分給 Muse Code。** Claude 主要負責 physics、審查和守規則；Codex 只做前端畫面；Antigravity 只做測試和部署。
- 每個用到 Meta 模型的地方，都要在畫面和報告上標明「由 Muse Spark / SAM 3.1 產生」，demo 時評審才看得到。

## Claude 是協調者（john 10/28 指定，最重要的規則之一）

**Claude Code 是大家的大腦，最清楚現在要做什麼。** Claude 寫在 `docs/STATUS.md` 的指示，等同 john 的指示。唯一的例外是下面的比賽硬規則和工程規則，這些連 Claude 也不能改。

john 睡覺或不在時：
1. **不要問 john 問題、不要停下來等。** 卡住就把問題寫進 STATUS 的「待 john 決定」，然後去做下一件。
2. **做完一件事就自己接下一件：**
    - 在 STATUS「完成表」裡你那一行打勾 `[x]`，並附上 commit 編號。
    - commit，再 push 到你自己的分支。不用等 john 說「可以 commit」，這條規則就是許可。
    - `git pull origin main`，重讀 STATUS，接完成表上你的下一個 `[ ]`。
    - 一直做到完成表沒有你的待辦為止。
3. **只 push 自己的分支**（`<工具>/<任務>-<短名>`），不要直接 push main。Claude 會審查並合併。
4. merge main 時 STATUS.md 衝突的處理：保留 main 的內容，再加上你自己的打勾和日誌。
5. 不要做完成表以外的事。不確定時，照 STATUS 的寫法做最小的版本。

## 目前方向：影片物理稽核（john 10/29 決定）

10/29 可行性關卡三題都通過（結果見 `docs/STATUS.md` 的「關卡結果」），john 選擇轉向**影片物理稽核**。
- 產品主線：使用者上傳拋物、掉落、彈跳或單擺的影片 → Muse 問清楚需要的資訊（物體、時間窗、鏡頭、尺寸、是否慢動作）→ SAM 3.1 追蹤（沒接上時用不用模型的顏色追蹤或 frame differencing）→ `physics/` 算數字 → 結果只說「與所假設的運動模型一致／不一致／資料不足」→ Spark 用使用者看得懂的話說明（數字由程式填入）。
- 任何工具都**不准**在畫面、文件或 demo 中宣稱「能辨識 AI 影片真偽」「能抓假影片」或「任何影片都能檢查」。不准寫哪支影片是哪家 AI 做的。只能說「與所假設的運動模型一致／不一致／無法判斷」。
- 斜坡教練不刪，保留成第二條路（「實驗教練」），只做維護，不再加新功能。
- demo 一定要同時放：真實影片一致、生成影片不一致、以及因為資料不足而拒判的例子。

## 文件優先順序

`docs/STATUS.md`（最新）＞ `AGENTS.md` ＞ `docs/PLAN.md`（10/25 的原始計畫）。三者衝突時以前面的為準。例如 PLAN.md 寫「排除語音」，但 10/27 已決定加入語音口述（T24），以 AGENTS.md 為準。

## 開工前必讀（每個 AI 每次都要做）

1. 讀 `docs/STATUS.md`：目前進度、誰在做什麼、缺什麼、已做的決定。
2. 只接 `docs/STATUS.md` 任務表中分配給你（或標「任何人」）且狀態為「待辦」的任務。開工時把狀態改成「進行中」並寫上你的名字。
3. 完成後，在同一個 commit 裡更新 `docs/STATUS.md`：任務狀態、完成內容、新發現的缺口、你做的決定。沒更新 STATUS 的工作視為沒完成。
4. 需要做規則外的決定（新套件、改資料格式、改 API）時，寫進 STATUS 的「待 john 決定」，不要自己拍板。
5. `docs/PLAN.md` 是完整計畫書（中文），有疑問先查它。
6. **所有共享資訊都寫進 `docs/STATUS.md`**（進度、決定、規程、給其他工具的話），不要另外開新的說明 .md 檔。研究成果（Manus）例外，放 `docs/research/`。

## 這個專案在做什麼

一個網站工具：檢查影片裡物體的運動，是否符合使用者假設的物理模型（自由落體／拋物、彈跳、單擺）。例如真實丟球的影片算出的重力接近 9.8 m/s²；一支生成影片算出 0.12 m/s²，就判「與真實重力的自由飛行不一致」，並列出原因、限制和原始數字。

物理模型以 `physics/experiments/<名稱>.py` 插件方式加入（freefall、pendulum、slope）。第一版只支援：固定鏡頭、近似正側視、單一物體。物體朝鏡頭方向移動（大小變化超過 30%）、慢動作、追蹤缺失時一律拒判。不做 3D、即時串流。

第二條路「實驗教練」（斜坡滑塊：先預測 → 實測 → 比較 → 下一次驗證）保留維護。

## 比賽硬規則（Meta Global AI Developer Hackathon，Indie 賽道）

- 截止：2026-11-04 21:00 ET（英國 11-05 02:00）。
- **產品執行時呼叫的 AI 模型只能是 Meta 模型**（Meta Model API 或 Meta 開放權重）。不准在產品程式碼裡呼叫 OpenAI、Anthropic、Google 等其他模型。
- 只算 2026-10-26 之後做的工作；repo 提交時必須公開；需要三分鐘 demo 影片。
- 不准把 API 金鑰寫進程式碼、commit、log 或任何 AI 對話。金鑰只放 `.env`（已在 `.gitignore`）。

## 不可違反的工程規則

1. **數字只由程式產生。** 長度換算、追蹤座標、曲線擬合、誤差、物理公式全部由 `physics/` 裡的確定性 Python 計算。模型不得產生、修改或「估計」任何測量數字。
2. **預測先鎖定。** prediction 在收到測試影片前保存，之後不可修改；重新校準要建新版本，保留舊版。
3. **不用測試影片調參。** 校準、開發、保留測試三組資料分開（見 `data/README.md`）。
4. **不把相關說成因果。** 模型輸出禁止「證實」「真因」「一定是」等字眼；只能說「與某假設一致」「目前無法區分」。後端要檢查。
5. **模型輸出要驗證。** 每次模型回傳都要通過 JSON schema、數值範圍、引用來源檢查；失敗就回到待確認狀態，不重試超過 2 次。
6. **缺資料就拒判。** 追蹤缺失、起滑時刻不明、校準不合格時，明確說不能判斷什麼，不插值掩蓋。
7. **花費上限。** 後端累計 Meta API 花費達 120 美元即拒絕新的付費呼叫（Meta 的花費通知不會停止扣款）。

## 技術選擇（要改先寫進「待 john 決定」）

- 後端：Python 3.11 + FastAPI。
- 數值：numpy、scipy；影片影格：ffmpeg。
- 前端：React + Vite + TypeScript，二維圖表。
- Meta Model API：`https://api.meta.ai/v1`，用 OpenAI Python SDK（`base_url` 指向上面，`api_key=os.environ["MODEL_API_KEY"]`）。
- 模型：`muse-spark-1.3`（主力）；`sam-3.1`（追蹤）；`muse-voice-transcribe-1.0`（語音口述，轉成文字後仍需使用者確認數字）；`muse-wonder-1.0` 只在 A/B 測試贏過 Spark 後才用。開發測試可用 `muse-spark-1.3-contributor`，但只能送 john 自己拍、沒有人臉的素材；使用者上傳的內容一律用標準版。

## 目錄結構（目標）

```
backend/      FastAPI、工作狀態、模型呼叫、輸出檢查、報告
physics/      校準、s(t) 轉換、擬合、比較（純函式 + 單元測試，不呼叫任何模型）
meta_client/  Meta Model API 包裝：spark、sam、wonder、花費計數
frontend/     五個畫面：場景設定、預測、影片分析、下一次驗證、實驗報告
data/         影片與人工標註（大檔不進 git，見 data/README.md）
docs/         STATUS.md、PLAN.md
tests/
```

## 分工（誰做什麼）

| 角色 | 負責 | 不要做 |
| --- | --- | --- |
| **Muse Code**（Meta） | `meta_client/` 全部、與 Meta API 相關的提示與工具定義、代理流程（選下一次驗證） | 改 `physics/` 的公式 |
| **Claude Code** | 架構、`physics/` 與其測試、`backend/` 的資料模型與輸出檢查、審查其他人的 PR | 寫前端樣式 |
| **Codex** | `frontend/` 五個畫面、曲線圖、影片疊加、報告匯出、補測試 | 改後端 API 契約（先提出） |
| **Antigravity** | 用內建瀏覽器跑端到端流程、截圖回報 UI 問題、部署腳本 | 大改架構 |
| **Manus** | 不碰程式碼。做研究與文件：競品比較、使用者測試計畫、demo 腳本與提交文字草稿；成果由 john 放進 `docs/` | 改 repo 程式 |
| **john** | 拍片、人工標註、決策、Discord、使用者測試、錄 demo | — |

前後端之間以 `docs/API.md` 的契約為準；要改契約先在 STATUS 寫提案。

## Git 規則

- 每個任務一個分支：`<工具>/<任務編號>-<短名>`，例如 `codex/T07-chart`。
- commit 訊息用英文，開頭寫任務編號：`T07: add trial chart`。
- 合併前至少跑 `pytest` 與前端 `npm test`；`physics/` 改動必須有測試。
