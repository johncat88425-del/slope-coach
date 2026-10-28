# STATUS：目前進度、缺什麼、誰在做

> 每個 AI 開工前讀這份，完成後在同一個 commit 更新這份。最新的放最上面。
> 最後更新：2026-10-27（Codex 完成 T08/T09 本機 mock 前端）

## 一句話現況

T08/T09 前端已放入 frontend/，分支 codex/T08-frontend。可選擇實拍照片／影片、保存校準草稿並在五頁間往返；目前本機 mock，尚未接後端追蹤與物理計算。尚未提供真實實驗影片或 API 實測結果。

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
| T06 | `physics/`：像素↔米校準、遮罩中心→s(t)、品質標記、定加速度擬合（a、v0、誤差）+ 測試 | Claude | 待辦 | 不呼叫模型 |
| T07 | `docs/API.md` 前後端契約初版 + `backend/` 骨架（experiment / trial / prediction / intervention） | Claude | 待辦 | T08 依賴它 |
| T08 | `frontend/` 骨架與五個畫面路由 | Codex | 完成 | React/Vite/TypeScript、五個 hash 路由、共用 Experiment；本機 mock 等 T07 |
| T09 | 校準點選畫面（點尺兩端、點滑塊） | Codex | 完成 | 原圖三點校準、撤銷、鍵盤座標替代、L/h 驗證與來源標示 |
| T10 | 預測鎖定 + 實測比較 + 曲線圖 | Claude（後端）/ Codex（圖） | 待辦 | |
| T11 | 釋放方式核對：受限驗證資料庫 + Spark 工具呼叫代理 | Muse | 待辦 | 只能從兩種驗證選 |
| T12 | 輸出檢查：schema、數字必須出自工具輸出、禁用因果字眼 | Claude | 待辦 | |
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
| T21 | 競品實測比較：PhET、Video2World、直接問 Muse | Manus | 待辦 | 成果放 docs/research/competitors.md |
| T22 | 使用者測試計畫：招募訊息、任務腳本、記錄表 | Manus | 待辦 | 11/02 要用，10/31 前完成 |
| T23 | 三分鐘 demo 分鏡與英文提交文字草稿 | Manus | 待辦 | 只寫已完成的功能，11/03 依實際結果修改 |

## 缺什麼（阻擋中或尚未知道）

- [ ] 尚缺真實實驗影片及後端整合；GitHub repo 與 T08/T09 前端已存在。
- [ ] docs/API.md 尚未定稿；校準版本、基準試驗、預測鎖定、上傳分析、驗證與報告等待 T07。
- [ ] 本機草稿在重新整理後清除，媒體不送到伺服器；持久化待後端契約。
- [ ] Meta API 金鑰與 150 美元額度是否已可用：未確認。
- [ ] 影片送 Spark 的實際 token 數與費用：未測（目前預算用假設值）。
- [ ] SAM 3.1 的 API 呼叫格式（影片怎麼上傳、遮罩怎麼回傳）：未讀官方範例。
- [ ] 評分權重：30/25/20/25 或四項等權，未確認。
- [ ] Muse Code 用 API 金鑰時是否扣 150 美元額度：官方說計費依金鑰帳戶，應該會扣，需看帳單確認。
- [ ] Discord「要用 Muse」的完整原文與是否允許其他 AI 寫程式：請 john 貼上原文。

## 待 john 決定

T08/T09 後端端點需求提案（路徑僅供 T07 討論，不是已定契約）：

| 建議方法／端點 | 前端需要的行為 |
| --- | --- |
| POST /experiments、GET /experiments/{id} | 建立／讀回同一份實驗紀錄與各步驟狀態 |
| POST /experiments/{id}/photos | 上傳實拍照片，回傳媒體 ID、原始寬高與讀取 URL |
| POST /experiments/{id}/calibrations | 以照片 ID、原始像素尺兩端/滑塊、尺距離/L/h（米）、使用者確認來源建立新版本；回傳品質檢查 |
| POST /experiments/{id}/trials | 建立基準或測試試驗；測試試驗綁定既有 prediction_id |
| POST /experiments/{id}/predictions | 依獨立基準與 calibration_version 建立不可修改的事前預測，附建立時間、假設與資料來源 |
| POST /trials/{id}/video | 鎖定預測後才接收測試影片；回傳媒體／工作 ID |
| POST /trials/{id}/analysis、GET /jobs/{id} | 啟動分析並輪詢處理／失敗／待確認；同一請求不可重複收費 |
| GET /trials/{id}/comparison | 已保存預測、實測時間/位置、缺失區段、品質標記及數字來源 |
| POST /experiments/{id}/interventions | 有據建議與使用者選擇分開，僅尺寸／釋放方式核對 |
| GET /experiments/{id}/report?format=markdown 或 csv | 匯出完整版本、試驗、來源與限制 |


## 已做的決定

- T08/T09：五個 hash 路由共用型別化 Experiment；路由變更與瀏覽器往返保留同一份紀錄。
- 校準標記以原始照片像素保存，僅做畫面座標映射；像素↔米、物理擬合仍由後端 physics 負責。
- L、h、尺距離標為「使用者量測並確認」；影像估計標為「尚無」。h ≥ L、任一尺寸 ≤ 0／空值／非有限數值、照片或標記不完整時拒絕保存。
- 保存校準採獨立快照，修改尺寸或標記使快照失效，換照片清除舊標記與拍攝確認。後端不可修改預測屬 T07/T10，本輪不假裝已實作。
- 不新增套件；npm test 使用既有 TypeScript 編譯和 Node 內建測試。預測／分析 mock 結果為空值，不以假數字當使用者實測；圖例為青色虛線與橘色實線。

| 日期 | 決定 | 原因 |
| --- | --- | --- |
| 10/27 | 產品內只呼叫 Meta 模型 | 比賽規則與工具運用分數 |
| 10/27 | 所有測量數字由 `physics/` 程式算，模型不碰數字 | 可重算、可檢查 |
| 10/27 | 保留斜坡核心，定位改為「動手之前先預測」的實驗教練；加語音口述（T24）；單擺（T25）為延伸 | john 選定：故事更大、多用一種 Meta 模型，又不犧牲可驗證性 |
| 10/27 | Muse Code 預設用 `muse-spark-1.3`，不用 Wonder 寫程式 | Wonder 每百萬輸出 token 20 美元，寫程式很快燒掉額度 |

## 成本紀錄（Meta API）

上限：150 美元額度；後端硬上限 120 美元。每天收工前填。

| 日期 | 項目 | 花費（美元） | 累計 |
| --- | --- | --- | --- |
| | | | 0 |

## 工作日誌（最新在上）

- 10/27 Codex：依 john 指定，將先前建立的前端移到 /Users/aacc/Documents/slope-coach/frontend/，以正式 repo 分支 codex/T08-frontend 工作；研究文件不納入此前端提交。
- 10/27 T08/T09 完成：五頁共用紀錄、照片三點校準與撤銷、原圖座標、鍵盤替代、圖片／影片錯誤處理、尺寸拒絕、校準保存快照、本機真實影片預覽。未接 API 的操作明確停用。
- 10/27 在正式 repo frontend/ 重跑 npm test：6 項通過；TypeScript/Vite production build 通過。原工作區瀏覽器已實查空白拒絕、圖片載入、三點輸入／直接點選／撤銷、h=L 拒絕、有效尺寸保存、五頁往返與報告顯示相同數值。UI 測試圖明示非實驗資料；沒有宣稱物理準確率。
- 10/27 pytest 曾嘗試但環境未安裝；本 repo 尚無 backend/physics 測試。本輪只提交分支，不合併。後續 T10/T13/T17 與語音 T24 仍依原分工與依賴執行。


- 10/27 建立 AGENTS.md、CLAUDE.md、STATUS.md 初版。
