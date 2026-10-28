# STATUS：目前進度、缺什麼、誰在做

> 每個 AI 開工前讀這份，完成後在同一個 commit 更新這份。最新的放最上面。
> 最後更新：2026-10-28（Claude：T12、T26 完成，審查 Codex T08/T09）

## 一句話現況

第 2 天（10/27）結束前：計畫書完成、比賽規則已查、Discord 回覆「要用 Muse」。**還沒有任何程式碼、影片或 API 測試結果。**

## 里程碑

| 日期 | 門檻 | 狀態 |
| --- | --- | --- |
| 10/28 | 能從一段影片量出可信的 s(t) | 未開始 |
| 10/30 | 整個循環跑通（含一種驗證） | 未開始 |
| 11/01 | 功能凍結 | 未開始 |
| 11/02 | 3–5 位使用者測試 | 未開始 |
| 11/03 | 部署、三次彩排 | 未開始 |
| 11/04 | 提交（英國 11/05 02:00 前，目標提早半天） | 未開始 |

## 任務表

狀態：待辦 / 進行中 / 完成 / 卡住。負責：Muse、Claude、Codex、Antigravity、john、任何人。

| 編號 | 任務 | 負責 | 狀態 | 備註 |
| --- | --- | --- | --- | --- |
| T01 | 建公開 GitHub repo，放入本資料夾的檔案，第一個 commit | john | 待辦 | |
| T02 | 安裝 Muse Code、Python 3.11、Node 20、ffmpeg、git | john | 待辦 | 見 README 的安裝清單 |
| T03 | 產生 Meta API 金鑰放進 `.env`；確認 150 美元額度已入帳；確認帳單是否綁卡 | john | 待辦 | |
| T04 | 搭器材，拍 3 段 5–15 秒測試片（固定手機、側視、尺入鏡） | john | 待辦 | |
| T05 | `meta_client/`：spark 呼叫（圖片、影片）、sam 追蹤、花費計數與 120 美元上限 | Muse | 待辦 | 先用 T04 的 1 段片實測 token 與費用，填入下方成本紀錄 |
| T06 | `physics/`：像素↔米校準、遮罩中心→s(t)、品質標記、定加速度擬合（a、v0、誤差）+ 測試 | Claude | 完成 | 分支 claude/T06-physics；23 個測試通過；另含 baseline、compare（拒判檢查）、diagnose（兩種驗證的證據） |
| T07 | `docs/API.md` 前後端契約初版 + `backend/` 骨架（experiment / trial / prediction / intervention） | Claude | 完成 | 分支 claude/T07-api（建在 T06 之上）；含 5 個 API 流程測試；Codex 請照 docs/API.md 接 |
| T08 | `frontend/` 骨架與五個畫面路由 | Codex | 待辦 | 等 T07 契約 |
| T09 | 校準點選畫面（點尺兩端、點滑塊） | Codex | 待辦 | |
| T10 | 預測鎖定 + 實測比較 + 曲線圖 | Claude（後端）/ Codex（圖） | 待辦 | |
| T11 | 釋放方式核對：受限驗證資料庫 + Spark 工具呼叫代理 | Muse | 待辦 | 只能從兩種驗證選 |
| T12 | 輸出檢查：schema、數字必須出自工具輸出、禁用因果字眼 | Claude | 完成 | backend/output_check.py；選驗證時的 model_rationale 會自動檢查；Muse 的說明文字也請呼叫 check_model_text() |
| T13 | 報告匯出（Markdown + CSV） | Codex | 待辦 | |
| T14 | 端到端瀏覽器測試與截圖 | Antigravity | 待辦 | T10 之後 |
| T15 | 拒判情境：遮擋、起滑不明、追蹤跳動 | Claude | 待辦 | |
| T16 | Spark 對 Wonder A/B（同一組開發片） | Muse | 待辦 | 10/31 |
| T17 | 影片預測疊加（限 2 小時） | Codex | 待辦 | 核心穩定後才做 |
| T18 | 尺寸核對（第二種驗證） | 任何人 | 待辦 | 時間不夠就砍 |
| T19 | 拍完 24 段片 + 人工標註（8 開發 / 6 校準 / 10 保留） | john | 待辦 | 標註不可用 AI |
| T20 | 部署、README、demo 錄影 | Antigravity / john | 待辦 | |
| T24 | 語音口述設定：Voice Transcribe 轉文字 → Spark 抽出欄位 → 使用者確認 | Muse | 待辦 | T11 之後做；數字一律要使用者確認 |
| T25 | 第二個實驗：單擺（沿用追蹤，換 physics/experiments/pendulum.py） | Claude | 待辦 | 10/30 循環跑通後才可開始，否則砍 |
| T26 | 後端資料持久化（重啟不清空） | Claude | 完成 | 每次寫入後存 data/store.pkl；設 SLOPE_STORE_PATH="" 可關閉 |
| T27 | 前端照 docs/API.md 接上後端（見下方「Claude 審查 Codex T08/T09」） | Codex | 待辦 | 先 merge main |
| T21 | 競品實測比較：PhET、Video2World、直接問 Muse | Manus | 待辦 | 成果放 docs/research/competitors.md |
| T22 | 使用者測試計畫：招募訊息、任務腳本、記錄表 | Manus | 待辦 | 11/02 要用，10/31 前完成 |
| T23 | 三分鐘 demo 分鏡與英文提交文字草稿 | Manus | 待辦 | 只寫已完成的功能，11/03 依實際結果修改 |

## 缺什麼（阻擋中或尚未知道）

- [ ] 還沒有真實影片；physics 門檻只用合成資料測過。
- [ ] requirements.txt 由 Antigravity（T02）建立；physics 和 backend 需要 fastapi、uvicorn、numpy、scipy、pytest、python-multipart、httpx（測試用）。
- [ ] Meta API 金鑰與 150 美元額度是否已可用：未確認。
- [ ] 影片送 Spark 的實際 token 數與費用：未測（目前預算用假設值）。
- [ ] SAM 3.1 的 API 呼叫格式（影片怎麼上傳、遮罩怎麼回傳）：未讀官方範例。
- [ ] 評分權重：30/25/20/25 或四項等權，未確認。
- [ ] Muse Code 用 API 金鑰時是否扣 150 美元額度：官方說計費依金鑰帳戶，應該會扣，需看帳單確認。
- [ ] Discord「要用 Muse」的完整原文與是否允許其他 AI 寫程式：請 john 貼上原文。

## Claude 審查 Codex T08/T09（給 Codex，T27）

前端做得很完整（校準驗證、來源標示、不假造數字都符合規則）。要接上 `docs/API.md` 時有這幾個差異：

1. **校準要多點一個點。** 後端需要 `path_start_px` 和 `path_end_px`（滑塊路徑的起點和終點）。前端目前是三點：尺兩端 + 滑塊。請把「滑塊位置」當成 `path_start_px`，再加第四點「滑塊會滑到的終點（坡底）」當成 `path_end_px`。
2. **上傳照片** 用 `POST /api/experiments/{eid}/scene-photo`（multipart `file`），回傳 `scene_check`；`needs_retake: true` 時顯示 `retake_reasons`。
3. **影片** 跟著 `POST /api/experiments/{eid}/trials` 一起上傳（multipart：`kind`、`calibration_version`、`file`）。test 試驗要在預測建立之後才上傳，否則比較時會得到 409。
4. **分析沒有 job 輪詢。** `POST /api/trials/{tid}/track` 是同步的；現在 SAM 還沒接，會回 501。收到 501 時，顯示「手動點選滑塊位置」模式，把點選結果用 `PUT /api/trials/{tid}/detections` 送出（`source: "manual"`）。
5. **起滑時刻** 要由使用者確認：先 `GET /release-suggestion` 拿建議（可能是空的），使用者確認後 `PUT /release-time`。
6. **比較** 是 `POST /api/experiments/{eid}/comparisons`，不是 GET。`verdict: insufficient_data` 是正常結果，要顯示沒通過的 `checks` 和 `can_still_say`。
7. **報告** 是 `GET /report.md` 和 `GET /report.csv`。
8. 你分支上的 STATUS.md 是根據舊版改的，merge main 時會有衝突：請保留 main 的內容，再加上你的更新。你之前在「待 john 決定」提的端點提案已經由 docs/API.md 取代，可以刪掉。

## 待 john 決定

- （無）

## 已做的決定

| 日期 | 決定 | 原因 |
| --- | --- | --- |
| 10/27 | 產品內只呼叫 Meta 模型 | 比賽規則與工具運用分數 |
| 10/27 | 所有測量數字由 `physics/` 程式算，模型不碰數字 | 可重算、可檢查 |
| 10/27 | 保留斜坡核心，定位改為「動手之前先預測」的實驗教練；加語音口述（T24）；單擺（T25）為延伸 | john 選定：故事更大、多用一種 Meta 模型，又不犧牲可驗證性 |
| 10/28 | 拒判門檻（開發值，會用真實影片調整）：可用影格 ≥ 80%（不阻擋，只提示）；起滑後至少 6 個可用點；擬合殘差 RMS ≤ 10 mm；前 20% 路程至少 3 點才可判斷初速度；差異門檻為到達時間相對誤差 15% 或基準變異的兩倍，取較大者 | PLAN 第二十五節：拒判不能只看可追蹤比例 |
| 10/28 | 下一次驗證的候選由 `physics/diagnose.py` 依數字產生（release_check / dimension_check），模型只能從中選擇與說明 | 模型不碰數字，也不能自創驗證 |
| 10/27 | Muse Code 預設用 `muse-spark-1.3`，不用 Wonder 寫程式 | Wonder 每百萬輸出 token 20 美元，寫程式很快燒掉額度 |

## 成本紀錄（Meta API）

上限：150 美元額度；後端硬上限 120 美元。每天收工前填。

| 日期 | 項目 | 花費（美元） | 累計 |
| --- | --- | --- | --- |
| | | | 0 |

## 工作日誌（最新在上）

- 10/28 Claude 完成 T12（模型輸出檢查：數字必須出自工具輸出、中英文因果誇大用語、驗證只能從證據候選選）與 T26（後端寫入後存檔）；審查 Codex 的 codex/T08-frontend，差異列在上方「Claude 審查 Codex T08/T09」。
- 10/28 Claude 完成 T07：docs/API.md 契約 v0.1 與 FastAPI 後端（記憶體儲存、預測鎖定、預測必須早於試驗、只能選證據支持的驗證、報告匯出）。Meta 模型接入點在 backend/model_hooks.py，Muse 實作後用 set_hooks() 換掉 MockHooks。
- 10/28 Claude 完成 T06 `physics/`：calibration、tracking、fit、experiments/slope、baseline、compare、diagnose，全部是純函式。用合成資料測過：正常、推出初速度、高度輸入錯誤、缺起滑時刻四種情境。
- 10/27 建立 AGENTS.md、CLAUDE.md、STATUS.md 初版。
