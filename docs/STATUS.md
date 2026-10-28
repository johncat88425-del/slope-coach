# STATUS：目前進度、缺什麼、誰在做

> 每個 AI 開工前讀這份，完成後在同一個 commit 更新這份。最新的放最上面。
> 最後更新：2026-10-27（Toronto；Codex 完成 T27/T10 前端/T13，整合 Claude T12/T15/T26）

## 一句話現況

前端已按 docs/API.md v0.1 接上真實 HTTP 呼叫，經 Vite proxy 連 localhost:8000。已串接實驗／照片／校準／試驗／起滑／基準／預測／比較／核對／報告，補上第四個路徑終點、501 手動替代、品質斷線圖及後端匯出。合成 API 閉環已通過；真實影片與 Meta 模型 hooks 尚未驗證。

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
| T08 | `frontend/` 骨架與五個畫面路由 | Codex | 完成 | 五路由共用後端紀錄；API v0.1 真實呼叫與 GET 恢復 |
| T09 | 校準點選畫面（點尺兩端、點滑塊） | Codex | 完成 | 原圖四點（尺兩端/滑塊即路徑起點/坡底終點）、校準新版本與來源標示 |
| T10 | 預測鎖定 + 實測比較 + 曲線圖 | Claude（後端）/ Codex（圖） | 進行中 | Codex 圖表與 API 串接完成；非 ok 區段斷線；合成閉環通過，仍待真片驗收 |
| T11 | 釋放方式核對：受限驗證資料庫 + Spark 工具呼叫代理 | Muse | 待辦 | 只能從兩種驗證選 |
| T12 | 輸出檢查：schema、數字必須出自工具輸出、禁用因果字眼 | Claude | 完成 | backend/output_check.py；選驗證時的 model_rationale 會自動檢查；Muse 的說明文字也請呼叫 check_model_text() |
| T13 | 報告匯出（Markdown + CSV） | Codex | 完成 | 直接下載後端 report.md / report.csv，保留來源與版本 |
| T14 | 端到端瀏覽器測試與截圖 | Antigravity | 待辦 | T10 之後 |
| T15 | 拒判情境：遮擋、起滑不明、追蹤跳動 | Claude | 完成 | 開頭被遮住時不判斷初速度並說明原因；偏離路徑的點不納入；4 個情境測試 |
| T16 | Spark 對 Wonder A/B（同一組開發片） | Muse | 待辦 | 10/31 |
| T17 | 影片預測疊加（限 2 小時） | Codex | 待辦 | 核心穩定後才做 |
| T18 | 尺寸核對（第二種驗證） | Muse | 待辦 | 時間不夠就砍 |
| T19 | 拍完 24 段片 + 人工標註（8 開發 / 6 校準 / 10 保留） | john | 待辦 | 標註不可用 AI |
| T20 | 部署、README、demo 錄影 | Antigravity / john | 待辦 | |
| T24 | 語音口述設定：Voice Transcribe 轉文字 → Spark 抽出欄位 → 使用者確認 | Muse | 待辦 | T11 之後做；數字一律要使用者確認 |
| T25 | 第二個實驗：單擺（沿用追蹤，換 physics/experiments/pendulum.py） | Muse（物理公式由 Claude 審查） | 待辦 | 10/30 循環跑通後才可開始，否則砍 |
| T26 | 後端資料持久化（重啟不清空） | Claude | 完成 | 每次寫入後存 data/store.pkl；設 SLOPE_STORE_PATH="" 可關閉 |
| T27 | 前端照 docs/API.md 接上後端（見下方「Claude 審查 Codex T08/T09」） | Codex | 完成 | 已合併最新 main；按審查採四點校準與 API v0.1 實際呼叫 |
| T28 | 結果說明層：Spark 讀 ComparisonOut，寫給使用者的中英文說明，先過 backend/output_check.check_model_text() 才顯示 | Muse | 待辦 | T11 之後；畫面標明「由 Muse Spark 產生」 |
| T29 | 在 backend 把 MockHooks 換成 MetaHooks（check_scene、track_slider、suggest_release_time） | Muse | 待辦 | T05 完成後馬上做；介面見 backend/model_hooks.py |
| T21 | 競品實測比較：PhET、Video2World、直接問 Muse | Manus | 待辦 | 成果放 docs/research/competitors.md |
| T22 | 使用者測試計畫：招募訊息、任務腳本、記錄表 | Manus | 待辦 | 11/02 要用，10/31 前完成 |
| T23 | 三分鐘 demo 分鏡與英文提交文字草稿 | Manus | 待辦 | 只寫已完成的功能，11/03 依實際結果修改 |

## 缺什麼（阻擋中或尚未知道）

- [ ] 後端傳回的 video_url 為 /media/...，但目前沒有對應檔案服務，scene-photo 也沒有可讀照片 URL。前端用本機選檔預覽；重新整理後需重選原片（不重複上傳）。請後端/部署負責工具補媒體存取。
- [ ] API CalibrationIn 沒有 slider_px 或照片 ID／影像尺寸欄位；滑塊標記與原圖尺寸目前只保留在前端草稿，尺／路徑幾何及尺寸才存後端。T07 是否擴充由 john/Claude 決定，前端未改契約。
- [ ] ModelHooks 仍為 mock：場景與起滑建議明列 mock，SAM 回 501；前端已有手動標記替代，不宣稱模型整合完成。
- [ ] T17 影片預測疊加尚未開始；待真實校準影片、可回查時間原點與可靠映射後驗證，不以合成測試圖代替真片對齊。

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

- 舊前端端點提案已由 docs/API.md v0.1 取代，不變更契約。後端 /media 存取仍需負責工具補齊；場景照片 URL 亦未提供。

## 已做的決定

- 前端以 /api 相對路徑呼叫，Vite proxy 目標 http://localhost:8000，避免 127.0.0.1 與 localhost 的 CORS 差異；部署需反向代理或指定 VITE_API_BASE_URL 並由後端設定 CORS。
- 只保存實驗 ID 於 localStorage，重新整理只 GET；寫入操作不自動重試。120 秒逾時提示先重新讀取紀錄，避免重複付費操作。
- 比較的 insufficient_data 視為正常結果；完整顯示 checks、can_still_say、finding 與 cannot_distinguish。核對選項只來自 evidence，使用者選擇標為 user，不假裝模型代理已接好。
- 圖表只顯示後端 physics 的曲線與實測；以已確認 t0 和 fit.s0_m 轉換繪圖座標，不自行擬合或調時間對齊。非 ok 樣本斷線，不補點。未有可靠起滑／擬合時不造實測線。
- SAM 501 轉手動逐影格點選；缺失標為 null，來源 manual。手動保存明示取代整份偵測資料；起滑候選不自動採用，須 user 確認。

| 日期 | 決定 | 原因 |
| --- | --- | --- |
| 10/27 | 產品內只呼叫 Meta 模型 | 比賽規則與工具運用分數 |
| 10/27 | 所有測量數字由 `physics/` 程式算，模型不碰數字 | 可重算、可檢查 |
| 10/27 | 保留斜坡核心，定位改為「動手之前先預測」的實驗教練；加語音口述（T24）；單擺（T25）為延伸 | john 選定：故事更大、多用一種 Meta 模型，又不犧牲可驗證性 |
| 10/28 | Muse 優先：產品裡的理解、判斷、說明都交給 Meta 模型，新的開發任務優先給 Muse Code；畫面與報告標明哪些由 Muse 產生 | john：要得名得主要用 Muse（評分有 Meta 工具運用一項） |
| 10/28 | 拒判門檻（開發值，會用真實影片調整）：可用影格 ≥ 80%（不阻擋，只提示）；起滑後至少 6 個可用點；擬合殘差 RMS ≤ 10 mm；前 20% 路程至少 3 點才可判斷初速度；差異門檻為到達時間相對誤差 15% 或基準變異的兩倍，取較大者 | PLAN 第二十五節：拒判不能只看可追蹤比例 |
| 10/28 | 下一次驗證的候選由 `physics/diagnose.py` 依數字產生（release_check / dimension_check），模型只能從中選擇與說明 | 模型不碰數字，也不能自創驗證 |
| 10/27 | Muse Code 預設用 `muse-spark-1.3`，不用 Wonder 寫程式 | Wonder 每百萬輸出 token 20 美元，寫程式很快燒掉額度 |

## 成本紀錄（Meta API）

上限：150 美元額度；後端硬上限 120 美元。每天收工前填。

| 日期 | 項目 | 花費（美元） | 累計 |
| --- | --- | --- | --- |
| | | | 0 |

## 工作日誌（最新在上）

- 10/27 Codex：再次整合 main 的 T15 拒判與 seed_demo（PR #3），保留所有 Claude 最新狀態；不改物理或後端。

- 10/27 Codex：git fetch origin 並合併 origin/main；STATUS 衝突合併保留 Claude T06/T07 與前端成果。GitHub 可見 main 包含 PR #1，另有 claude/T06-physics、claude/T07-api；當時未見其他工具的新分支成果；後續又合併 PR #2 的 T12/T26。
- 10/27 Codex：依最新 main 的 T27 審查，改為四點校準（滑塊位置即路徑起點）並保留 Claude T12/T26 的狀態與紀錄。共用 checkout 被其他工具切分支後，已將自己的前端提交移回 Codex；後續改用隔離 worktree 完成以避免混入別人的分支。
- 10/27 Codex 完成前端 API 串接及 T10 前端／T13：建立/恢復實驗、照片與重拍原因、校準版本、baseline/test/intervention 上傳、追蹤501替代、起滑、三段基準、鎖定預測、比較及品質斷線圖、有限核對與結果連結、MD/CSV 匯出。未修改 backend/physics 或 API 契約。
- 10/27 驗證：npm test 14 項通過、TypeScript/Vite build 通過、合併最新 T12/T15/T26 後 pytest 40 項通過（1 個 Starlette/httpx 棄用提示）。Python 系統環境故障，改用 app bundled Python 3.12 與 /tmp 隔離依賴執行，未改專案 Python 3.11 技術選擇。
- 10/27 真實 HTTP 整合：前端 compiled API client → Vite proxy → FastAPI，合成資料由現有 physics Python 產生且實驗標題明示 SYNTHETIC；跑過三段基準、兩個不可修改預測、資料不足／差異／重做一致、501、校準422、核對建立/連結、MD/CSV。這是傳輸與流程驗證，不是真片準確率。
- 10/27 瀏覽器實查：讀回上述後端紀錄、版本/試驗來源顯示、501 切手動、insufficient_data 展示 failed checks 與 can_still_say。截圖另存輸出 api-insufficient-data.png，無付費模型呼叫。

- 10/28 Claude 完成 T15，並新增 `scripts/seed_demo.py`：後端開著時執行 `python -m scripts.seed_demo --case pushed`（或 wrong_height / ok / occluded），會建立一個用合成資料的完整實驗，前端和 Antigravity 不用真影片也能測整個流程。四種情境結果：pushed→建議釋放核對、wrong_height→建議尺寸核對、ok→一致、occluded→有差異但證據不足、不建議任何驗證。
- 10/28 Claude 完成 T12（模型輸出檢查：數字必須出自工具輸出、中英文因果誇大用語、驗證只能從證據候選選）與 T26（後端寫入後存檔）；審查 Codex 的 codex/T08-frontend，差異列在上方「Claude 審查 Codex T08/T09」。
- 10/28 Claude 完成 T07：docs/API.md 契約 v0.1 與 FastAPI 後端（記憶體儲存、預測鎖定、預測必須早於試驗、只能選證據支持的驗證、報告匯出）。Meta 模型接入點在 backend/model_hooks.py，Muse 實作後用 set_hooks() 換掉 MockHooks。
- 10/28 Claude 完成 T06 `physics/`：calibration、tracking、fit、experiments/slope、baseline、compare、diagnose，全部是純函式。用合成資料測過：正常、推出初速度、高度輸入錯誤、缺起滑時刻四種情境。
- 10/27 建立 AGENTS.md、CLAUDE.md、STATUS.md 初版。
