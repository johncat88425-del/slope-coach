# STATUS：共享工作檔（所有資料都在這裡）

> 每個 AI 開工前讀這份，完成後在同一個 commit 更新這份。不要另外開新的說明檔，新資訊直接寫進這份的對應段落。
> **Claude 是協調者**：這份檔裡 Claude 寫的指示等同 john 的指示。john 不在時不要問問題，做完就打勾、commit、push，再接下一件（規則見 AGENTS.md）。
> 最後更新：2026-10-29 06:40Z（Claude）

## 一句話現況

**10/29 03:10 可行性關卡三題都通過，john 決定轉向「影片物理稽核」。** john 自拍的 2 支影片算出 g = 9.62、9.82（一致）；6 支 Meta AI 影片全部不一致，最明顯的一支 g = 0.12。現在最大的缺口是**追蹤品質**：不用模型的追蹤在 3 支 Meta 影片上不可靠，Manus 那支咖啡色的球也追不到，所以 **SAM 3.1（Muse T38）是第一優先**。斜坡教練保留，只做維護。

## 現在每個工具要做什麼（10/29 03:40 Claude 指示，給一整晚的量，照順序做，做完一件就接下一件）

john 睡覺時：不要問問題、不要停。做完一件就打勾、附 commit、push 自己的分支，再 `git pull origin main` 接下一件。卡住寫進「待 john 決定」，然後跳下一件。

| 誰 | 照這個順序做 | 重點 |
| --- | --- | --- |
| **Muse**（最優先） | （T05–T67 已合併）→ **T107 SAM 全部重跑** → **T112 說明與標題接上稽核** → T108 → T109 → T110 → T111 | SAM 是最大的缺口：顏色追蹤在 Meta clip1、4、5 和 Manus 那支失敗，測試影片在 repo 的 `data/gate/clips/`（之前寫的 /mnt/ 路徑只在 Claude 的雲端電腦上，你那邊沒有，是 Claude 的錯）。所有用到模型的輸出都要標來源；數字只能由 physics 產生。花費超過 10 美元先停，寫進 STATUS。 |
| **Codex** | T143 → T146 → T151 → T145 → T149 → T150（T100–T142 已完成並合併） | demo 用的資料都在 `data/demo/`（`real_own_*`、`generated_*`）。不准出現「偵測 AI」「假影片」「真假」。 |
| **Antigravity** | （T02 已由 Claude 做完）T52 → T42 → T119 → T120 → T121 → T122 → T54 → T53 | **10/29 john 已在 Mac 設好 `gh auth login`，現在 push 得上去了**（之前 Muse 推不上去就是這個原因）。不要再做 3D 渲染影片。部署帳號等 john 決定。 |
| **Manus** | T23 → T95 → T123 → T124 → T125 → T126 | 只寫文件，交給 john 轉給 Claude。數字只用 `data/gate/product_results.md`。 |
| **Claude** | T127 → T129 → T128 → T130 → T131 | 每 2 小時巡查、審查合併。 |
| **john**（明天） | 把 Manus 的文件傳給 Claude；看 demo 導覽；可選：Kling／Luma 各生成 1 支 | 錄 demo 前先讓 Claude 確認數字。 |

**重要（10/29 09:00 Claude）：做完一件不要結束對話。** 昨晚大家做完手上的任務就停了，因為沒有人叫你們再看一次 STATUS。規則是：做完一件 → push → `git pull origin main` → 重讀這份 → 接下一個 `[ ]`，一直做到你那一區沒有 `[ ]` 為止。只有全部做完才結束，結束前在工作日誌寫一行「XX 沒有待辦了」。卡住（缺檔案、缺權限）就寫進「待 john 決定」，然後跳下一件，不要停在那裡等。

## 完成表（每做完一件就打勾，附 commit；Claude 每隔一段時間來看）

格式：`- [x] 編號 負責 內容 — commit abc1234`。只改你自己那一行，不要刪別人的行。

**Muse**（照順序做）
- [x] T05 Muse：`meta_client/`（Spark、SAM 3.1、花費計數與 120 美元上限、mock 測試）— commit b696c68
- [x] T29 Muse：後端接上 MetaHooks（沒有金鑰時退回 Mock）— commit b696c68
- [x] T34 Muse：Spark 建議運動片段 `suggest_motion_segment`。只回傳建議，不回傳測量數字，要通過 schema 檢查 — commit b696c68
- [x] T38 Muse：（後端介面已由 Claude 在 T84 做好，你只要在 MetaHooks 實作 `track_object`，呼叫 SAM 3.1，座標正規化規則見 docs/API.md v0.5）在 ModelHooks 加 `track_object(video_path, text_prompt, t_start, t_end)`，由 SAM 3.1 回傳每格的中心和面積，讓 `backend/audits.py` 可以改用 SAM（`track_source: "sam"`）。沒接上時維持 frame_diff — commit b696c68（真片實測 75 格 65 中，$0.015）
- [x] T39 Muse：Spark 檢查稽核影片的拍攝條件，包括鏡頭是否固定、是否近似側視、物體是否全程入鏡。只回傳布林值和原因，結果給使用者確認 — commit b696c68
- [x] T28 Muse：結果說明層。Spark 讀 `ComparisonOut` 或 `AuditOut` 寫說明，先過 `check_model_text()` 才顯示，畫面標明「由 Muse Spark 產生」。不准出現「真／假影片」「AI 生成」等字眼 — commit b696c68
- [x] T11 Muse：下一次驗證的選擇代理（只能從 evidence 候選中選）— commit b696c68
- [x] T24 Muse：語音口述設定（Voice Transcribe 轉文字，Spark 抽出欄位，使用者確認）— commit b696c68
- [x] T16 Muse：Spark 與 Wonder 的 A/B 比較腳本。先用 mock 跑通，實際呼叫限 1 美元以內，花費記進成本紀錄 — commit b696c68
- [x] T45 Muse：稽核代理。Spark 用工具呼叫，從固定清單（free_flight、bounce、persistence）選要跑哪些檢查，並說明理由。數字只來自工具輸出，理由先過 `check_model_text()`。這是「創意使用 Meta AI」的主要展示點 — commit 5c4d8a7（propose_plan 改 rationale_template＋{check_key} 槽位，fill_numbers 填入；拒絕裸數字/未知槽；8 測試）
- [x] T46 Muse：Spark 準確度評估腳本。對 `data/gate/manifest.csv` 裡的影片，比較 Spark 建議的時間窗和物體，跟 john 的人工標註差多少，結果寫進 STATUS。只能送沒有人臉的影片 — commit b696c68
- [x] T47 Muse：英文版的說明文字（給評審看），同樣要過 `check_model_text()` — commit b696c68
- [x] T66 Muse：**Muse 偵訊**（特色功能）。後端契約已完成（docs/API.md v0.4、T78）：你只要在 MetaHooks 實作 `interview_audit(video_path) -> AuditInterview`，讓 Spark 看幾張畫面、回傳最多 3 題 `{field, text}`，後端會自動檢查，不通過就退回固定問題。下判定之前，Spark 先看影片的幾張畫面，向使用者提出最多 3 個問題，例如「有沒有開慢動作？」「鏡頭有沒有動？」「這顆球大概多大？」。使用者的回答變成確認過的輸入（`camera_static`、`object_size_m`、時間窗），Spark 不能自己填數字。畫面像一段問答，標明「由 Muse Spark 提問」 — commit 20f4337（真片實測 3 題全過）
- [x] T67 Muse：**物理名片標題**（特色功能）。Spark 依照 `AuditOut` 的數字，為結果寫一句好記的標題，例如「這顆球落得像在月球上：表觀重力只有地球的 0.26 倍」。Spark 只寫 `{g_vs_earth:2}`、`{nearest_body}` 這種欄位位置，再交給 `backend.output_check.fill_numbers()` 填入數字並檢查，不通過就不顯示。不准出現真、假、AI 生成等字眼 — commit bacce3f（meta_client/headline.py：{nearest_body} 字串槽程式代換＋fill_numbers 數字槽＋check＋真/假/AI 字禁令；insufficient_data/無重力數字回 None 不呼叫 API；4 測試；全套件 185 pass）

- [x] T107 Muse：SAM 3.1 全部重跑 — commit 4971cec（7 支 track_source 全 sam 但全拒判：後端分母用 24fps、SAM 只出 15fps，天花板 62.5% < 0.8；已寫進待 john 決定等 Claude 修。$0.077，累計 $0.167）。**影片已經放進 repo 的 `data/gate/clips/`**（Meta 6 支＋Manus 1 支；john 自己拍的 3 支不進 git，沒有就列成 missing，沒關係）。步驟：
    1. `git pull origin main`，確認 `.env` 有 `MODEL_API_KEY`，`pip install -r requirements.txt`
    2. `set -a; . ./.env; set +a; python -m scripts.audit_batch data/gate/manifest.csv --out data/gate/product_results_sam.md`（有金鑰時後端會自動用 SAM 追蹤；表格的 track_source 欄要是 sam）
    3. 把 `product_results_sam.md` 的表格貼到 STATUS「關卡結果」下面的新小節「SAM 對照」，和 `data/gate/product_results.md`（顏色追蹤版）並排。兩版都要報告，不准只放好看的，也不准改 manifest 的標註
    4. 花費記進成本紀錄，commit `data/gate/product_results_sam.md`＋STATUS，push 分支 `muse/T107-sam-rerun`
- [ ] T108 Muse：Spark 看第一格畫面，建議 `object_name`（例如 orange basketball）和「鏡頭看起來固定嗎」。只是建議，要使用者確認才會用；回傳要過 schema 和 `check_model_text`
- [ ] T109 Muse：語音回答偵訊問題：`muse-voice-transcribe-1.0` 把使用者說的話轉成文字，Spark 抽出欄位（例如物體大小），**數字一定要使用者在畫面上確認**才送出。沒有金鑰時用 mock
- [ ] T110 Muse：花費顯示：後端 `/api/spend` 回傳目前累計花費和 120 美元上限，給前端顯示。到上限時所有付費呼叫拒絕，並有測試
- [ ] T111 Muse：每一個用到 Meta 模型的回傳都帶 `source`（model 名稱與版本），讓畫面能標示「由 Muse Spark 1.3 產生」「由 SAM 3.1 追蹤」
- [ ] T112 Muse：（後端已由 Claude T143 做好）在 `MetaHooks` 加兩個方法：`explain_audit(audit: dict) -> str | None` 呼叫 `explain.explain_result(audit, kind="audit")`，`headline_audit(audit: dict) -> str | None` 呼叫 `headline.write_headline(audit)`。失敗就回 None 或丟例外，後端會退回固定模板，也會再檢查一次數字和禁用字。用 john 的 own_2 和 meta clip2 真打各一次，結果和花費寫進 STATUS

**Codex**（PR #4 合併後才開始，照順序做）
- [x] T36a Codex：`vite.config.ts` 加上 `/media` 代理，校準畫面改用 `photo_url` — commit 7596711（17 項前端測試、build；pytest 50 pass/1 skip：缺 ffmpeg）
- [x] T36b Codex：軌跡疊加圖與 2D 軌跡圖元件。實測點用橘色，有缺口的地方不連線 — commit f2c750f
- [x] T36c Codex：所有 Meta 模型產生的內容標明「由 Muse Spark／SAM 3.1 產生」 — commit 0faeb49
- [x] T40 Codex：新畫面「檢查影片」：上傳影片、選時間窗、勾選鏡頭固定、輸入物體尺寸，接 `POST /api/audits`（見 docs/API.md v0.2）。顯示 verdict、reasons、numbers、疊加圖、軌跡圖、limits。`insufficient_data` 是正常結果。畫面文字只准說「與自由落體模型一致／不一致／無法判斷」 — commit 4aa759f
- [x] T41 Codex：「檢查影片」畫面的 npm 測試，包括三種 verdict 的顯示，以及確認畫面沒有「真／假／AI 生成」字眼 — commit 94a8ec0
- [x] T13b Codex：稽核結果匯出成 Markdown（數字照後端給的，不自己算） — commit b1f833a
- [x] T17 Codex：影片預測疊加（限 2 小時） — commit 7addfc7；預設關閉，須使用者核對影像尺度/起點/時間；真片對齊仍待驗收
- [x] T48 Codex：介面中英文切換，預設英文，因為評審看英文 — commit 6790495
- [x] T49 Codex：首頁說明「這個工具能判斷什麼、不能判斷什麼」，照 docs/research/competitors.md 的結論寫，不准說「第一個」 — commit 9bfc41f
- [x] T50 Codex：demo 模式：讀取事先存好的稽核結果 JSON，讓 demo 不用連網或等追蹤 — commit 1abd274
- [x] T51 Codex：手機版排版與無障礙（色盲也能分辨預測線和實測線，不能只靠顏色） — commit 77ab223
- [x] T59 Codex：「檢查影片」和離線重播支援 `assumed_model=bounce`（顯示 `rebound_ratio_k`）。目前離線重播只接受 free_flight，會擋掉 bounce 結果 — commit fa8fcbe
- [x] T60 Codex：稽核結果顯示 `events`（消失、大小跳動、位置跳動）的時間軸，以及 `size_trend` 拒判的說明文字 — commit 8e3162c
- [x] T61 Codex：稽核結果的網址可以直接打開（`#/audits/:id`，用 `GET /api/audits/{id}`） — commit 977ccae
- [x] T62 Codex：demo 品質：上傳進度、處理中狀態、422／404／網路錯誤的友善訊息（照後端的 reason 顯示，不改寫數字） — commit 3a5d622
- [x] T63 Codex：在主要按鈕和結果區塊加上 `data-testid`，給 Antigravity 的端到端測試用，並把清單寫進 STATUS — commit 4a163b7
- [x] T64 Codex：**鬼影對照**（特色功能，demo 主畫面）。在影片和軌跡圖上，把 `ghost_points` 畫成半透明的「鬼影球」，跟著影片時間和真的物體一起移動。真的物體用實線，鬼影用虛線，加上圖例「如果遵守 9.81 m/s² 會在這裡」。差距大的地方標出最大差距的像素數（數字由前端從兩組點相減，只做顯示，不做判定） — commit 676467f
- [x] T71 Codex：「檢查影片」加入單擺選項：選 pendulum 時顯示「擺長（公尺，可留空）」欄位並送 `length_m`，結果顯示 `period_s`、`implied_length_m`、`predicted_period_s`；離線重播也要接受 pendulum — commit c6ce3d4
- [x] T65 Codex：**物理名片**（特色功能）。把一次稽核結果做成一張可以下載成 PNG 的卡片，內容包括疊加圖縮圖、判定、`nearest_body` 和 `g_vs_earth`（例如「重力像在月球：地球的 0.26 倍」）、`implied_time_factor`（「影片大約是真實速度的 0.5 倍」）、`implied_object_size_m`（「如果這是真的，這顆球直徑 2.4 公尺」）、`g_verdict_robust` 為 0 時的提醒、limits，以及「由 Muse Spark 撰寫說明」的標示。標題位置先放 T67 的空位 — commit dbf8587
- [x] T74 Codex：**對照展示頁**（demo 用）。把一致、不一致、拒判三種結果並排放在同一頁，每一張都有鬼影對照和物理名片縮圖。資料先讀 `data/demo/synthetic_*.json`（頁面上要寫明 SYNTHETIC，是程式畫的測試方塊），等 john 的真實影片跑完再換成真的結果。目的：demo 時評審一眼看到「會判一致、會判不一致、也會拒判」 — commit 81f3f65
- [x] T75 Codex：數字顯示格式。畫面和名片上的數字只做顯示用的四捨五入（例如 g_vs_earth 顯示 0.26、尺寸顯示 2.4 m），匯出的 JSON 保留原值。不准改變數值本身 — commit 52f4c34
- [x] T76 Codex：彈跳結果圖。用 `rebound_ratio_k` 畫每次反彈高度比例的長條圖，加一條 1.0 的參考線（超過 1.0 代表反彈得比上一次高，與被動彈跳模型不一致） — commit c55ae96
- [x] T77 Codex：「Muse 偵訊」問答面板的外觀（給 Muse T66 用）。先用固定的假問題做畫面，標示 mock；契約已在 docs/API.md v0.4：先 `POST /api/audit-drafts` 拿到問題，再用 `draft_id` 和使用者的回答呼叫 `POST /api/audits`；`slow_motion` 是新欄位。mock 問題現在後端就會回傳，可以直接接 — commit 2c8bcd2
- [x] T80 Codex：修正 `formatNumber`：尺寸和長度目前只留 1 位小數，0.067 m 會顯示成「0.1」，會誤導使用者。改成 3 位有效數字（0.067、2.40、0.250），並補測試 — commit ab4d467
- [x] T81 Codex：**demo 導覽模式**。加一個「Guided demo」按鈕，按照順序帶評審看：首頁說明（能判斷什麼、不能判斷什麼）→ Muse 偵訊 → 結果與鬼影對照 → 物理名片 → 三種結果並排。每一步用一句英文說明，加上「Next」按鈕，並標明哪些內容由 Muse Spark 產生。只用已經有的畫面，不新增假資料 — commit c4b1481
- [x] T82 Codex：英文介面文字總檢查，給評審看的。統一用語（consistent / inconsistent / insufficient data with the assumed model），刪掉內部用語（例如 fixture、draft id），按鈕文字要短。不准出現 real、fake、AI-generated、detect — commit 6b73368
- [x] T85 Codex：「檢查影片」和 Muse 偵訊加一個「物體名稱」欄位，送 `object_name`（給 SAM 的文字提示，預設 ball）。結果區要依照 `track_source` 標明「由 SAM 3.1 追蹤」或「frame differencing（未使用模型）」，物理名片和匯出也要寫（API v0.5） — commit 8a7bd26
- [x] T101 Codex：「結果牆」頁：讀 `data/demo/real_own_*.json` 和 `data/demo/generated_*.json`（`generated_clip: true`，`source` 是 meta_ai 或 manus），每支一張卡：來源、判定、`explanation.text`、最接近的星球、追蹤來源。全部列出，不挑片；資料不足的也要放，並顯示原因。頁首一句話：「同一套規則跑過每一支影片；結果只說和假設的運動模型是否一致」。不准寫「偵測」「假影片」 — commit 4d85fad
- [x] T102 Codex：鬼影球播放：結果頁加「播放」按鈕，用 `points` 和 `ghost_points` 依時間同步動畫兩顆點（實際的球和照地球重力的球），沒有影片也能播。只用後端給的座標，不自己算物理 — commit 9a68187
- [x] T103 Codex：重力刻度尺：在結果頁畫一條對數刻度（冥王星 0.62、月球 1.62、火星 3.71、地球 9.81、木星 24.79），標出 `g_apparent_m_s2` 和 `g_apparent_low/high` 的範圍。星球數值直接寫在前端常數，量測值只用後端數字 — commit ddf0f3c
- [x] T104 Codex：上傳頁加「拍攝檢查清單」：鏡頭固定、側面拍、只有一個物體、顏色鮮明（例如橘色）的球、不要慢動作、球不要朝鏡頭飛。附一句：「不符合時系統會拒判，不會硬給答案」 — commit 883190a
- [x] T105 Codex：手機版與無障礙檢查：稽核首頁、結果頁、結果牆在 390 px 寬不能橫向捲動；按鈕可用鍵盤操作；圖表有文字替代 — commit d3afe11
- [x] T100 Codex：（T92 之後做）結果區最上面顯示 `explanation.text`，旁邊標明來源：`template` →「固定模板（未使用模型）」，`model` →「由 Muse Spark 產生」。名片和匯出也要放。不要改寫文字或數字 — commit c2fdeaf
- [x] T92 Codex：（T89、T90 之後做）稽核變成網站首頁：打開網站先看到「檢查影片」與 demo 導覽；斜坡教練移到第二個分頁「實驗教練」，功能不刪。首頁一句話說明：「檢查影片中的運動是否符合你假設的物理模型」，不准出現「AI 偵測」「抓假影片」等字 — commit c0c6758
- [x] T89 Codex：檢查並修飾 Claude 在 T88 對前端的最小改動（`track_source: "color"` → 「顏色＋移動追蹤（未使用模型）」），樣式和其他來源標籤一致，補一個測試 — commit 46fccb8
- [x] T90 Codex：demo 導覽加「真實影片」一段，讀 `data/demo/real_own_1.json` 到 `real_own_3.json`（`real_clip: true`）。要標明「john 自己拍的影片、標註由 john 確認」，並把 own_1、own_2 的「一致、最接近地球」和 own_3 的「不一致、原因不明」放在一起，不挑片。這些紀錄沒有影片（`video_url` 是空字串，john 的家不放上公開 repo），要能正常顯示軌跡、鬼影和數字 — commit f5103e9
- [x] T86 Codex：結果、名片和匯出都要顯示使用者回答的 `slow_motion`。如果是因為慢動作被拒判，要用一句話說明原因（直接照後端的 reason，不要自己改寫） — commit d560608

- [x] T113 Codex：稽核執行中的進度提示（上傳中、追蹤中、計算中），稽核可能要 10 秒以上；失敗時顯示後端的錯誤原因，不要只寫「失敗」 — commit 31543d9
- [x] T114 Codex：真實 vs 生成並排比較頁：選兩筆紀錄（例如 `real_own_2` 和 `generated_meta_clip2`），左右並排顯示軌跡、鬼影、重力刻度和說明。標題寫「同一套規則，兩支影片」，不准寫「真假」 — commit 843d762
- [x] T115 Codex：稽核報告列印版（CSS print stylesheet），一頁 A4 放：判定、說明、數字、軌跡圖、限制、追蹤來源與模型來源標示 — commit 9e810e1
- [x] T116 Codex：Muse 語音回答的介面（配合 Muse T109）：錄音按鈕 → 顯示轉出的文字和抽出的欄位 → 使用者逐欄確認後才送出。沒接上時按鈕顯示「需要 Meta API」 — commit 3f85efa
- [x] T117 Codex：英文介面全面檢查（評審看英文）：所有新頁面都要有英文，用詞照 AGENTS 規則（consistent／inconsistent／insufficient data with the assumed model） — commit fa18e96
- [x] T118 Codex：首頁 30 秒自動導覽模式（給 demo 錄影用）：依序顯示 real_own_2 → generated_meta_clip2 → generated_meta_clip4（拒判），每步有一句英文說明，可暫停 — commit 9428051

- [x] T142 Codex：（T133 之後做）時間窗選擇器加「建議的時間窗」按鈕：呼叫 `POST /api/audit-drafts/{id}/windows`，把候選畫成時間軸上的色塊，點一下就把把手移過去，使用者還是要按「確認時間窗」。標明「由程式建議（未使用模型）」 — commit 593ecf8
- [x] T133 Codex：上傳後可以在瀏覽器預覽影片，拖動兩個把手選 `t_start`、`t_end`（顯示到 0.01 秒），使用者按「確認時間窗」才送出。時間只來自使用者操作，前端不猜 — commit 66249bc
- [x] T135 Codex：「How it works」頁（英文為主）：流程圖 Muse 問問題 → SAM 3.1／顏色追蹤 → physics 擬合 → 判定 → 說明，每一步標明「Meta model」或「deterministic code」，並標出目前哪些是 mock（照 `track_source`、`explanation.source` 的實際值，不要寫死成已接上） — commit 8499d85
- [x] T136 Codex：首頁給評審的開場區：一句話說明 + 三張卡片（real_own_2 一致、generated_meta_clip2 不一致、generated_meta_clip4 資料不足），點下去開那筆紀錄 — commit cc65c0a
- [x] T137 Codex：分享連結：`/audit/<audit_id>` 直接顯示已存的結果（GET /api/audits/{aid}），加「複製連結」按鈕；找不到時顯示清楚的錯誤 — commit a25a94b
- [x] T138 Codex：純靜態 demo 模式：`VITE_DEMO_ONLY=1` 時只讀 `data/demo/` 的紀錄、不呼叫後端，上傳按鈕顯示「demo 版不能上傳」。這樣沒有後端也能給評審看。build 指令寫進 STATUS — commit 04a747a
- [x] T139 Codex：效能：大頁面拆分載入，production build 的主 bundle 降到 250 kB 以下（gzip 前），把數字寫進 STATUS — commit b3717c3
- [x] T140 Codex：容錯測試：`points` 是空的、`numbers` 缺欄位、`explanation` 不存在、`nearest_body` 是 null 時，每個結果元件都不會壞掉，並補測試 — commit 041eb73
- [ ] T143 Codex：（API v0.9）結果區和物理名片最上面顯示 `headline.text`（有的時候才顯示），旁邊標明「由 Muse Spark 撰寫」；`headline` 是 null 時照舊用程式產生的標題。不要改寫文字或數字。靜態 demo 資料裡 `headline` 一律是 null
- [ ] T146 Codex：結果區加「這次用了哪些 Meta 模型」小面板：照實際值列出提問（`interview.source`）、追蹤（`track_source`）、說明（`explanation.source`）、標題（`headline` 有沒有）。是 mock、template、color、frame_diff 的，要寫「未使用模型」，不准寫死成已接上
- [ ] T151 Codex：拒判（`insufficient_data`）時顯示「怎麼重拍」提示：用固定對照表把 `reasons` 對應到提示，例如鏡頭移動 → 用腳架、物體朝鏡頭移動 → 從側面拍、慢動作 → 用正常速度。不用模型，並補測試
- [ ] T145 Codex：右上角顯示 Meta API 花費（配合 Muse T110 的 `GET /api/spend`）。端點還不存在（404）時就不顯示，不要放假數字
- [ ] T149 Codex：T133–T142 的新元件補齊繁中和英文切換，加測試確認沒有漏翻的字串
- [ ] T150 Codex：時間窗選擇器的鍵盤操作（方向鍵移動把手、Enter 確認）和螢幕閱讀器標籤，補測試

**Antigravity**（照順序做）
- [x] T02 Antigravity→Claude：（10/29 06:40 Antigravity 整晚沒有 push，改由 Claude 做）`requirements.txt`、`scripts/dev.sh`（檢查 ffmpeg／python3／npm，缺什麼就列出 brew 指令；後端 8000、前端 5173；沒有金鑰時用 mock） — 見 PR T02
- [ ] T14 Antigravity：用 `seed_demo` 跑斜坡流程的端到端測試，截圖放 `docs/screenshots/`，問題寫進「缺什麼」
- [ ] T42 Antigravity：稽核流程的端到端測試。用 `tests/scripts/test_gate_run.py` 的 `write_clip` 產生合成影片，經 API 或畫面跑一次正常 g 和 g/4 兩種情況，截圖
- [ ] T43 Antigravity：部署草稿：Dockerfile 與啟動說明。只在本機測，不要公開部署；`.env` 不准進映像檔
- [ ] T44 Antigravity：README 的安裝與使用說明（英文），只寫已經能用的功能
- [ ] T52 Antigravity：GitHub Actions CI：每個 PR 自動跑 `pytest` 和 `npm test`（需要安裝 ffmpeg）
- [ ] T53 Antigravity：效能測試：一支 30 秒 1080p 的 iPhone HEVC 影片，用 `/api/audits` 稽核要花多久，目標 20 秒內，結果寫進 STATUS
- [ ] T68 Antigravity：鬼影對照和物理名片的端到端測試與截圖（等 T64、T65 合併後做）
- [ ] T54 Antigravity：上傳安全：檔案大小上限 200 MB、只收影片格式、每個 IP 每天最多 20 次稽核。寫成提案放進「待 john 決定」，Claude 審查後實作

- [ ] T119 Antigravity：用 `docker compose up` 一個指令就能跑起前後端（含 ffmpeg），只在本機測。要部署到哪個網站先寫進「待 john 決定」，不要自己開帳號
- [ ] T120 Antigravity：端到端測試：結果牆（T101）、鬼影球播放（T102）、並排比較（T114），桌機和 390 px 手機各截圖，放 `docs/screens/`（只放圖片）
- [ ] T121 Antigravity：效能量測：一支 10 秒 1080p 的影片跑完 `/api/audits` 要多久（顏色追蹤和 frame differencing 各一次），結果寫進 STATUS；超過 20 秒就在 STATUS 提出可以縮短的地方，不要自己改 physics
- [ ] T122 Antigravity：在乾淨環境照 README 從零安裝一次，把卡住的步驟寫進 STATUS

**Manus**（不寫程式）
- [x] T21 Manus：影片物理合理性競品研究（附來源），結果放在 `docs/research/competitors.md`
- [x] T23 Manus：demo 分鏡與提交文字（兩個版本，未完成的部分寫 [TBD]）。差異點照 competitors.md 的結論寫，不准說「第一個」或「偵測 AI 影片」。**10/29 改成單一版本：影片物理稽核**（真實影片一致 → Meta 影片不一致 → 拒判例子 → Muse 問問題與說明）
- [x] T95 Manus：提交頁文字草稿（英文，300 字以內）：問題、做法、Meta 模型用在哪、限制。數字只能引用 STATUS「關卡結果」，不准說「偵測 AI 影片」
- [ ] T22 Manus：使用者測試計畫（招募訊息、任務腳本、記錄表）

- [x] T123 Manus：三分鐘英文旁白稿，逐秒對應 T23 分鏡；只用 `data/gate/product_results.md` 裡的數字
- [x] T124 Manus：評分標準對照表：Impact 30%、Meta 工具運用 25%、技術深度 20%、Demo 25%，每一項寫我們的證據（指到 repo 裡的檔案或 demo 片段），做不到的老實寫「沒有」
- [x] T125 Manus：使用者測試計畫改版（取代 T22）：找 5 個人用自己的手機拍丟球影片上傳，記錄他們能不能看懂結果、哪裡卡住。附招募訊息和記錄表
- [x] T126 Manus：限制與常見問題（英文 FAQ）：為什麼不判斷真假、為什麼會拒判、需要怎麼拍、數字怎麼來、Meta 模型做了什麼

**Claude**
- [x] T141 Claude：候選時間窗：`physics.experiments.freefall.suggest_flight_windows` 和 `POST /api/audit-drafts/{id}/windows`（API v0.8）。在 john 的 3 支影片上，第一個或第二個候選和 john 的標註差不到 0.2 秒（own_1 1.87–2.60、own_2 0.03–0.80、own_3 1.82–2.42）。只是建議，關卡和稽核仍然只用人確認的時間窗 — 見 PR T141
- [x] T143 Claude：稽核結果接上 Muse 的說明和標題（API v0.9）：後端呼叫 hook `explain_audit`、`headline_audit`，模型的文字要再過一次 `check_model_text`（數字要能在結果裡找到，四捨五入後也算；不能有禁用字）才會用，否則退回固定模板。模型看不到原始軌跡，判定和數字都不經過模型；模型失敗也不會讓稽核壞掉 — 見 PR T143
- [x] T144 Claude：生成影片（Meta 6 支、Manus 1 支，共 11 MB，沒有個人隱私）放進 `data/gate/clips/`。`audit_batch --clips` 預設讀這裡，找不到的影片列成 missing。john 自己拍的影片不進 git — 見 PR T144
- [ ] T127 Claude：審查並合併所有工具的 PR（每 2 小時巡查一次）
- [x] T128 Claude：顏色追蹤支援更多顏色（yellow、green、red），只對**之後新的影片**生效，記進規則變更紀錄，關卡已跑的結果不重算
- [x] T129 Claude：`gate_run` 報告多加一欄 `size_trend`（只顯示，不當規則），讓關卡表和網站結果表能對照 — 見 PR T129
- [x] T130 Claude：（10/29 03:50 Manus 的 T23、T95、T123–T126 已檢查入庫：`docs/research/manus_t23_t95_t123_t126.md`。用詞符合規則，數字都來自 product_results，Muse/SAM 標 TBD）把 Manus 交來的 T23、T95、T123–T126 檢查用詞和數字後放進 `docs/research/`
- [ ] T131 Claude：彈跳和單擺的真實影片流程（等 john 拍片）：準備標註表和試跑腳本
- [x] T106 Claude：`data/demo/generated_*.json`：6 支 Meta、1 支 Manus 影片經網站流程的完整結果（含說明，不含影片），給 Codex T101 結果牆用 — 見 PR
- [x] T99 Claude：稽核結果新增 `explanation`（API v0.7），先用固定模板寫一般人看得懂的說明，數字由 `fill_numbers` 填入，例如「the object falls as if gravity were 1.71 m/s², 0.17 times Earth's, closest to Moon」。Muse T45 接上後改成 `source: model`。`data/demo/real_own_*.json` 已重新產生，含說明 — 見 PR T99
- [x] T98 Claude：`scripts/audit_batch.py`：把 manifest 裡每支影片都走一遍網站流程，產生 `data/gate/product_results.md`（網站判定結果表）。demo 和提交文字的數字引用這張表。目前：自拍 2 一致、1 小幅不一致；Meta 2 不一致（月球、冥王星）、4 資料不足（球朝鏡頭飛）；Manus 1 資料不足 — 見 PR T98
- [ ] T96 Claude：（Manus 已補，03:15）Manus 1 支、Antigravity 2 支（程式渲染 3D，另列「程式模擬」來源）標註好後補進關卡紀錄
- [x] T97 Claude：`output_check` 加上新方向的禁用語（抓假、測謊、AI 偵測、任何影片、lie detector、any video 等），並加測試 — 見 PR T97
- [x] T31 拋體檢查、T32 關卡工具、T35 彈跳與持續性檢查、T30 `/media`
- [x] 審查並合併 Muse 的 T05、T29（10/29 04:10 連同 T38、T66、T45、T67 一起合併）
- [x] 審查並合併 Codex PR #4 與 #16（T36–T51，含 #4 的內容）：pytest 58、npm 37、build 都通過；前端沒有自己算物理，畫面沒有「真／假／AI 生成」字眼
- [x] T37 Claude：後端稽核端點 `POST /api/audits`、`GET /api/audits/{aid}`（docs/API.md v0.2）
- [x] T32 跑關卡：三題都通過（自拍 3、Meta AI 6），方向等 john 決定
- [x] T91 Claude：`data/demo/real_own_1..3.json`：john 3 支真實影片經 `/api/audits` 的完整結果（顏色追蹤、0.11 m），給 demo 和 Codex T90 用；不含影片和疊加圖 — 見 PR T91
- [x] T88 Claude：網站的「檢查影片」沒接 SAM 時，物體名稱有顏色（如 `orange ball`）就用 T87 的顏色追蹤，`track_source: "color"`（API v0.6）。前端只加了最小的型別與標籤，讓畫面不會拒收；Codex 請檢查文字和樣式。用 john 的 3 支影片走網站流程：g = 9.62、9.81、8.15，和關卡一致 — 見 PR T88
- [x] T87 Claude：不用模型的顏色＋移動追蹤（`backend/video.track_color`）。人工標註的物體名稱有顏色（例如 `orange ball`）時，關卡改用它；`--tracker frame_diff` 可重現舊規則。球的大小改用短軸寬度，不受動態模糊影響。3 支真實影片的紅點都落在球上 — 見 PR T87
- [x] T55 Claude：稽核支援 `assumed_model=bounce`（接上 `check_bounces`）
- [x] T56 Claude：透視檢查：物體大小沿軌跡變化超過 30% 時拒判（`physics/persistence.size_trend`）
- [x] T57 Claude：單擺 physics 插件 `physics/experiments/pendulum.py`（週期、等時性、由週期推算擺長），給稽核和教練兩條路共用；尚未接到 API
- [x] T58 Claude：驗證報告產生器：`gate_run` 的輸出最後會附上「## Summary」，列出各來源的一致、不一致、資料不足、拒判支數，並逐題算出三個關卡問題是 pass、fail 還是 pending（等 john 看疊加圖）。所有影片都列入，不挑片
- [x] T69 Claude：鬼影軌跡與星球比喻的後端（`physics/experiments/freefall.ghost_track`、`nearest_body`，API v0.3 的 `ghost_points`、`nearest_body`），以及尺寸誤差 ±30% 的穩健度（`g_apparent_low/high`、`g_verdict_robust`）
- [x] T70 Claude：單擺接上 `/api/audits`（`assumed_model=pendulum`，可選 `length_m`），見 docs/API.md v0.3
- [x] T72 Claude：模型文字檢查加上真偽字眼黑名單（真／假影片、AI 生成、deepfake 等一律擋下），以及 `fill_numbers()`：模型只寫欄位位置，數字由程式填入（給 T67、T28 用）
- [x] T73 Claude：合成測試資料 `data/demo/synthetic_*.json`，用 `python -m scripts.synthetic_audits` 重新產生。這是真的 `/api/audits` 輸出，但影片是程式畫的方塊，共 6 種：正常 g、g/4、鏡頭移動、彈跳變低、彈跳變高、單擺。檔案裡有 `synthetic: true`，只能拿來開發和測試，demo 不准說成真實或生成的影片。Codex 做 T64、T65、T71，Antigravity 做 T68 時，可以先用這些檔案
- [x] T78 Claude：Muse 偵訊的後端：`POST /api/audit-drafts`、`interview_audit` hook（含 mock）、問題檢查（不准有數字和違規字眼，最多 3 題）、`draft_id` 與 `slow_motion` 欄位（API v0.4）
- [x] T79 Claude：`scripts/gate_prepare.py`：列出每支關卡影片的 fps、長度、尺寸（fps 超過 90 會提醒可能是慢動作），產生附時間戳的縮圖總表方便 john 看出時間窗，並在 manifest 加上標註留空的列。不呼叫模型，也不自動填標註
- [x] T83 Claude：關卡工具用合成影片從頭到尾試跑過一次（prepare → 標註 → run → 總表）。修正一個問題：還沒標註的影片原本會被算成「拒判」，現在改成「unlabelled」，不列入任何計數，總表另外列出。門檻沒有改
- [x] T84 Claude：稽核接上 SAM 的後端介面 `track_object`（MockHooks 會丟出 TrackingUnavailable，後端自動改用 frame differencing）。新增 `object_name` 欄位，`track_source` 會標明實際用了哪一種，API v0.5
- [ ] 審查 Muse、Codex、Antigravity 的所有 PR

**john**
- [ ] T33 拍片並生成影片，提供標註
- [x] 合併 PR #4（已隨 PR #16 一起合併）
- [ ] 在 Discord 問：用其他工具生成的影片當測試素材可不可以

## 可行性關卡：影片物理稽核（10/28–10/29）

**主張：** 這支影片裡的物體運動，是否違反這次檢查所假設的運動模型（固定重力下的拋體或自由落體）。
- **不准宣稱：** 任何工具都不准在畫面、文件或 demo 中說「能辨識 AI 影片真偽」或「任何影片都能檢查」。只能說「與所假設的運動模型一致」、「不一致」或「無法判斷」。
- **影片來源只記錄，不當答案：** 不把影片分成「真實」和「AI」來打分。
- **少量素材只回答「值不值得繼續」：** 不能用來證明產品可靠。

**規則已凍結。** 門檻在看到任何關卡影片之前就寫進 `scripts/gate_run.py` 的 `GATE_RULES` 和 `physics/experiments/freefall.py` 的預設值，所有影片用同一個指令跑：

```
python -m scripts.gate_prepare /mnt/project-files/gate   # 先做：縮圖總表在 data/gate/sheets/，manifest 新增空白列給 john 填
python -m scripts.gate_run data/gate/manifest.csv --clips /mnt/project-files/gate --out data/gate/results.md --overlays data/gate/overlays
```

### 三個問題與通過條件

1. **能不能在真實影片上量到可信的軌跡？** 用 john 自己拍的影片（鏡頭固定、正側面、物體尺寸已知），3 支裡至少 2 支要同時做到三件事：沒被拒判、判定一致、量出的 g 在 9.81 ± 15% 內。john 要看過疊加圖，確認追蹤點落在物體上。john 自己拍的影片如果被判「不一致」，就算誤報，要逐一說明原因。
2. **能不能找到有清楚證據的異常，而不是追蹤或拍攝誤差？** 至少 1 支影片（不限來源）被判「不一致」，而且要同時符合四個條件：
    - 追蹤到的畫面比例 ≥ 80%。
    - john 看過疊加圖，確認追蹤點落在物體上。
    - john 標註鏡頭是固定的。
    - 物體尺寸估錯 30% 時異常仍然成立：以 g 為根據的異常，g 要偏離 9.81 超過 50%。方向偏差超過 15°，或殘差超過移動距離 2%，則直接算數。
3. **能不能用同一套規則處理所有案例，不為了 demo 逐片調參？** 一個指令、一個 commit 跑完；每支影片唯一的輸入是 john 的人工標註；被拒判的影片不超過一半。看過資料後如果改了規則，要記進下方「規則變更紀錄」，用新規則全部重跑，並同時報告新舊兩版的結果。

### 決定規則

- **三題都通過：** 轉向「影片物理稽核」，由 Claude 改寫 AGENTS.md、本檔和 demo 劇本。
- **大部分案例都要拒判，或找不到足以支持主張的異常：** 回到「實驗調查員」，也就是把斜坡的真實實驗閉環做好。拋體檢查留下來，當第二個實驗插件。
- 不論走哪條路，都照兩條原則做：成功和拒判放在同一段 demo 裡；只承諾已經做完的東西。

### 關卡素材（john 準備，T33）

影片放在 `/mnt/project-files/gate/`。影片檔不進 git。

- **自己拍至少 3 支：**
    - 丟一顆尺寸已知的球（網球、乒乓球都可以），讓它劃出弧線。
    - 手機放在支架上，從正側面拍，整段飛行都要入鏡。
    - 用一般 60fps 錄，**不要用慢動作**。背景要素，人不要入鏡。
    - 可以加拍 1 支手持、鏡頭會動的影片，測試拒判。
- **生成 5 到 10 支：** 優先用 Meta AI app。提示範例：`Static camera, side view. A tennis ball is tossed in an arc across a plain white room and lands on the floor.` 有彈跳的影片，只標第一次落地前的那段。
- **人工標註：** 由 john 告訴 Claude，再由 Claude 寫進 `data/gate/manifest.csv`。標註不准用 AI 產生。

| 欄位 | 意思 |
| --- | --- |
| clip | 檔名 |
| source | own（自己拍）、generated（生成）或 other。只記錄，不當答案 |
| assumed_model | 目前只有 `free_flight` |
| t_start、t_end | 物體離手到落地前的時間（秒） |
| camera_static | yes 或 no |
| object、object_size_m | 物體名稱和直徑（公尺），由 john 填 |
| track_ok | john 看過疊加圖後填 yes 或 no（追蹤點有沒有落在物體上）。先留空，第一次跑完再填 |

### 已知限制（結果裡要照實寫）

- 關卡的追蹤用畫面差異法，不用模型。物體有動態模糊時，尺寸會估大，g 也會跟著偏。
- 沒有處理透視：物體朝鏡頭或遠離鏡頭飛時，結果不可信。
- 時間窗目前由人標註。正式版改由 Spark 建議（T34），使用者確認。

### 規則變更紀錄

- **10/29 T87（看過 john 的 3 支自拍影片之後改的）**：原規則用 frame differencing，在真實影片上抓到手臂和背景。新規則：人工標註的物體名稱含顏色（目前只有 orange，色相 15 到 45 度、飽和度與亮度至少 0.4）時，只取「是這個顏色而且有在動」的最大一塊；物體大小改用色塊短軸的寬度。其他門檻不變。顏色範圍是看過這 3 支影片後訂的，所以**之後的 Meta AI 影片要用同一組參數，不准再調**。
- 新舊兩版用同一組試算標註（Claude 提議、john 尚未確認：own_1 1.9–2.6 s、own_2 0.2–0.8 s、own_3 2.0–2.4 s，球 0.05 m）的結果：
  - 舊版 frame_diff：own_1 不一致（加速度偏 -70 度、軌跡不像拋物線）、own_2 不一致（-71 度）、own_3 資料不足。原因是追到手臂，不是物理。
  - 新版 color：三支軌跡都是乾淨拋物線（殘差只有行程的 0.4% 到 0.8%，偏角 1 到 6 度），但算出的 g 只有 3.7 到 4.5 m/s²。換句話說，如果 g 是 9.81，球的直徑應該是 0.11 到 0.13 m，不是 0.05 m。三支都偏同一個方向，比較像是尺寸標註的問題，所以先請 john 用尺量球（圓周 ÷ 3.14）。**不准為了讓結果變成一致去改門檻或改顏色參數。**

- **10/29 03:45 T128**：顏色追蹤加上 yellow、green、blue、red（red 跨 0 度）。只對之後新的影片生效，關卡已跑的結果不重算；orange 的參數不變。

### 關卡結果

**10/29 03:10 正式結果：三題都通過（用 T87 之後的規則）**（`data/gate/results.md`；舊規則版本 `results_frame_diff.md`）

| 來源 | 一致 | 不一致 | 資料不足 | 拒判 |
| --- | --- | --- | --- | --- |
| 自拍（john） | 2 | 1 | 0 | 0 |
| Meta AI 生成 | 0 | 6 | 0 | 0 |

- Q1 **pass**：own_1 g = 9.62、own_2 g = 9.82，john 確認紅點在球上。
- Q2 **pass**：john 確認追蹤正確的 3 支 Meta 影片（clip2、3、6）都是明確異常。例如 clip6 的軌跡是乾淨拋物線（殘差 1.8%），但 g 只有 0.12 m/s²（落下約 0.9 m 花了約 3.5 秒）。clip1、4、5 john 判定追蹤不可靠（`track_ok = no`），不拿來當證據。
- Q3 **pass**：9 支都用同一套規則，0 支拒判。
- 舊規則（frame_diff）：Q1 fail，因為追到手臂。

**要誠實寫出來的限制：**
1. 顏色追蹤是看過 john 的 3 支自拍之後才加的（見規則變更紀錄）。Meta 影片是在規則定下之後才生成、才跑的，沒有再調參數。
2. 網站稽核比關卡更保守。它多了「物體大小沿軌跡變化超過 30% 就拒判」這條透視檢查（T56，看資料前就有）。同樣 6 支 Meta 影片，網站判 clip2（g 像月球）、clip3（g 像冥王星）不一致，另外 4 支因為球朝鏡頭飛而判資料不足。demo 和文件要用網站的結果。
3. 目前只有一家生成模型（Meta AI），每家 1 支只是試驗。不能說「能檢查任何影片」或「能辨識 AI 影片」。
4. 10/29 03:15 補進 Manus 生成 1 支：john 判定球是橘黑色，物體名稱填 `orange basketball`。顏色追蹤只追到 55% 的格數，所以**拒判**（照規則，沒有改標註去湊結果）；改用 frame_diff 的試跑是 g = 2.55，只當參考。加入後 Q3 是 1/10 拒判，仍然 pass。還沒列入關卡的：Antigravity 和 john 從 Gemini 拿到的影片各 2 支，都是**程式畫出來的動畫**（Lavf 編碼、簡單 3D 或平面畫面），不是生成式影片模型做的，另列「程式模擬」來源，不算進 Q2。後者不是生成式 AI，屬於「程式模擬」類；試跑 ag_clip1 得到 g = 23.75，最接近木星。

**10/29 02:30 第一次正式試跑**（john 量的球直徑 0.11 m；john 10/29 02:28 確認時間窗，並確認三張疊加圖的紅點都在球上；`data/gate/results.md`，舊規則版本在 `results_frame_diff.md`）

| 影片 | 新版（顏色追蹤） | 舊版（frame_diff） |
| --- | --- | --- |
| own_1 | 一致，g = 9.62 | 不一致（追到手臂） |
| own_2 | 一致，g = 9.82 | 不一致（追到手臂） |
| own_3 | 不一致，g = 8.17（超出 ±15% 的下限 8.34 一點點） | 資料不足 |

- Q1 自拍影片追得準：**pass**。2 支一致而且 g 在 15% 以內，john 確認紅點在球上（`track_ok` = yes）。
- Q2 找得到明確異常：**fail（目前）**。還沒有 Meta AI 影片，這題要等 john 的 5 到 10 支生成影片。
- Q3 同一套規則、拒判不超過一半：**pass**（0/3 拒判）。
- own_3 是自拍影片上的誤報，要說明：它的 g 只差 17%，沒有到「明確異常」（差 50%）的程度。一開始猜是球朝鏡頭移動，但網站稽核量到的球大小沿軌跡只變 -3%，不支持這個猜測，**原因目前不明**。用 ±30% 尺寸誤差算，這個判斷不穩健（`g_verdict_robust` = 0），所以不算明確異常。沒有調參。

### SAM 對照（10/29 Muse T107：同一 manifest 用 SAM 3.1 重跑，`data/gate/product_results_sam.md`）

| clip | source | verdict | g_apparent_m_s2 | nearest_body | size_trend | track_source | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | missing |  |  |  |  | not found in data/gate/clips |
| own_2_IMG_8429.mov | own | missing |  |  |  |  | not found in data/gate/clips |
| own_3_IMG_8434.mov | own | missing |  |  |  |  | not found in data/gate/clips |
| meta_clip1.mp4 | meta_ai | insufficient_data |  |  |  | sam | object tracked in only 62% of frames |
| meta_clip2.mp4 | meta_ai | insufficient_data |  |  |  | sam | object tracked in only 63% of frames |
| meta_clip3.mp4 | meta_ai | insufficient_data |  |  |  | sam | object tracked in only 62% of frames |
| meta_clip4.mp4 | meta_ai | insufficient_data |  |  |  | sam | object tracked in only 63% of frames |
| meta_clip5.mp4 | meta_ai | insufficient_data |  |  |  | sam | object tracked in only 61% of frames |
| meta_clip6.mp4 | meta_ai | insufficient_data |  |  |  | sam | object tracked in only 62% of frames |
| manus_clip1.mp4 | manus | insufficient_data |  |  |  | sam | object tracked in only 61% of frames |

和顏色追蹤版（`data/gate/product_results.md`）並排：顏色版 meta 是 2 不一致（clip2 g=1.71 像月球、clip3 g=0.26 像冥王星）＋4 資料不足（透視拒判），Manus 那支 55% 拒判；SAM 版 7 支全部因「只追到六成格數」拒判，**目前 SAM 版一個數字都算不出來**。兩版都照實報告，不只放好看的；manifest 沒動。

**原因（不是追蹤品質，是分母算錯）**：7 支的 61–63% 完全一致，因為這是 15/24 = 62.5%。SAM 照 T05 規格先降到 15fps 再追，後端 `audits.py` 的覆蓋率卻用來源片格數（24fps）當分母（`frac = len(pts)/len(frames)`，門檻 0.8）。SAM 在 24fps 片子上天花板就是 62.5%，永遠過不了。修法在後端（Claude 的範圍）：分母改用追蹤器的預期格數；另外 `by_t` 用時間戳精確對齊，15fps 的時間戳很少落在 24fps 格點上，下游的 events／鬼影對齊也要一起修。修好之前 SAM 版數字不能引用。own_3 支不在 git 裡所以是 missing（預期內）。

## 任務表

狀態：待辦、進行中、完成、卡住。

| 編號 | 任務 | 負責 | 狀態 | 備註 |
| --- | --- | --- | --- | --- |
| T32 | 可行性關卡：凍結規則、`scripts/gate_run.py`、疊加圖、10/29 填結果 | Claude | 進行中 | 工具完成，等影片 |
| T33 | 拍 3 支以上丟球影片、生成 5–10 支影片，並提供人工標註 | john | 待辦 | 見上方「關卡素材」 |
| T34 | Spark 建議運動片段：`suggest_motion_segment(video)` 回傳 `object`、`assumed_model`（只能是 free_flight、slide 或 none）、`candidate_t_start`、`candidate_t_end`、`reason` | Muse | 完成 | commit b696c68 |
| T38 | MetaHooks 實作 `track_object`（SAM 3.1，正規化座標），audits 可改用 SAM | Muse | 完成 | commit b696c68；真片 75 格 65 中；缺口：官方 4 支測試片不在本機 |
| T39 | Spark 檢查拍攝條件（鏡頭固定、近似側視、物體全程入鏡），只回布林值和原因 | Muse | 完成 | commit b696c68 |
| T46 | Spark 準確度評估：建議時間窗/物體 vs 人工標註 | Muse | 完成 | commit b696c68；等 T33 影片實測 |
| T47 | 英文版說明文字（給評審），同樣過 check | Muse | 完成 | commit b696c68 |
| T45 | 稽核代理理由改用 fill_numbers 寫法（模型只寫欄位位置） | Muse | 完成 | commit 5c4d8a7；propose_plan rationale_template＋槽位；拒絕裸數字/未知槽；8 測試通過 |
| T66 | Muse 偵訊：Spark 看幾張畫面問最多 3 題，答案變確認輸入 | Muse | 完成 | commit 20f4337；驗證鏡像後端檢查；6 測試；真片實測通過 |
| T67 | 物理名片標題：Spark 寫 {g_vs_earth:2}＋{nearest_body} 槽模板，程式填入驗證 | Muse | 完成 | commit bacce3f；禁真/假/AI 字；無重力數字不顯示；4 測試 |
| T35 | physics：彈跳檢查（每次反彈高度要變低）、物體持續性檢查（突然消失、面積跳動、分裂） | Claude | 完成 | `freefall.check_bounces`、`physics/persistence.py`；合成資料測試；尚未接進關卡（關卡規則已凍結，只用 free_flight） |
| T36 | 前端：`/media` 代理、軌跡疊加圖、2D 軌跡圖元件、Meta 產生內容的標示 | Codex | 待辦 | PR #4 合併後再做 |
| T05 | `meta_client/`：Spark（圖片、影片）、SAM 3.1 追蹤、花費計數與 120 美元上限 | Muse | 完成 | commit b696c68；SAM 已真片實測（$0.015），Spark 影片費用待測 |
| T29 | 後端把 MockHooks 換成 MetaHooks（check_scene、track_slider、suggest_release_time） | Muse | 完成 | commit b696c68；有 key 才切換 |
| T02 | 開發環境：requirements.txt、`scripts/dev.sh`、檢查 Python 3.11、Node 20、ffmpeg | Antigravity | 待辦 | 不要用 sudo 自己裝，列出指令給 john |
| T14 | 端到端瀏覽器測試與截圖（先用 seed_demo 的合成資料） | Antigravity | 待辦 | 截圖放 `docs/screenshots/` |
| T21 | 競品研究：影片物理合理性工具（VideoPhy、Physics-IQ、Tracker）、PhET；確認我們的差異 | Manus | 待辦 | 每個結論附來源 |
| T22 | 使用者測試計畫 | Manus | 待辦 | 10/31 前 |
| T23 | 三分鐘 demo 分鏡與英文提交文字草稿（兩個版本） | Manus | 待辦 | 未完成的寫 [TBD] |
| T27 | 前端照 docs/API.md 接上後端 | Codex | 完成 | PR #4 已審查通過，等 john 按 Ready for review 後合併 |
| T11 | 下一次驗證的選擇代理（只能從 evidence 候選中選） | Muse | 完成 | commit b696c68 |
| T28 | 結果說明層：Spark 讀比較結果寫說明，先過 `check_model_text()` 才顯示 | Muse | 完成 | commit b696c68 |
| T24 | 語音口述設定（Voice Transcribe → Spark 抽欄位 → 使用者確認） | Muse | 完成 | commit b696c68 |
| T16 | Spark 與 Wonder 的 A/B 比較 | Muse | 完成 | commit b696c68；mock 跑通，實測待命 |
| T17 | 影片預測疊加（限 2 小時） | Codex | 待辦 | |
| T20 | 部署、README、demo 錄影 | Antigravity、john | 待辦 | 11/03 |
| T31 | physics：拋體與掉落軌跡檢查（`physics/experiments/freefall.py`） | Claude | 完成 | |
| T30 | 後端 `/media` 提供上傳的影片和照片；場景照片回傳 `photo_url` | Claude | 完成 | 前端代理在 T36 |
| T26 | 後端資料持久化 | Claude | 完成 | 存在 data/store.pkl；設 `SLOPE_STORE_PATH=""` 可關閉 |
| T15 | 拒判情境（遮擋、起滑不明、追蹤跳動） | Claude | 完成 | |
| T12 | 模型輸出檢查（數字必須出自工具輸出、禁止因果誇大用語） | Claude | 完成 | `backend/output_check.py` |
| T08–T10、T13 | 前端五個畫面、校準、曲線圖、報告匯出 | Codex | 完成 | 在 PR #4 裡 |
| T06、T07 | physics 斜坡模型、API 契約與後端 | Claude | 完成 | `docs/API.md` |
| T01 | 建立公開 repo | john | 完成 | |
| T03 | Meta API 金鑰放進 `.env`，確認 150 美元額度 | john | 待辦 | 金鑰不准貼給任何 AI |
| T18、T19、T25 | 尺寸核對、24 段實驗片、單擺 | Muse、john | 暫停 | 關卡結果出來後再決定 |

## 怎麼跑（給所有工具）

- 後端：`uvicorn backend.main:app --reload`，網址 http://localhost:8000，互動文件在 `/docs`。API 契約見 `docs/API.md`。
- 合成示範資料：`python -m scripts.seed_demo --case pushed`，也可以把 case 換成 wrong_height、ok 或 occluded。
- 測試：`pytest`（目前 58 個通過）；前端 `cd frontend && npm test`。
- 免模型的軌跡探測：`python -m scripts.flight_probe 影片.mp4 --start 1.0 --end 2.0 --overlay out.png`。
- 上傳的檔案由後端放在 `/media/{eid}/{檔名}`。

## 缺什麼

- [ ] 還沒有可用的真實影片。第一支（IMG_8418.MOV）有四個問題：拍攝角度是斜的、滑塊太小太淡、只滑了 0.75 秒、畫面有人臉。
- [x] Meta API 金鑰與額度是否可用：可用。Muse 10/29 用 .env 金鑰真打 SAM 成功（75 格 $0.015）。
- [ ] 影片送 Spark 的實際 token 數和費用：未測。
- [x] SAM 3.1 API 的格式：已讀官方文件並實測（commit b696c68；Responses API + Files API，遮罩 base85 用官方解析器）。
- [x] T38 官方測試片不在 Muse 的電腦上 → 10/29 Claude 已把生成影片放進 `data/gate/clips/`（T144）
- [ ] `tests/scripts/test_gate_prepare.py` 在乾淨 main 上也失敗（Muse 10/29 驗證過，與 Muse 改動無關）：gate_prepare 處理真片時 exit 1。請 Claude/Antigravity 修，T52 CI 會踩到。
- [ ] 用其他工具生成的影片當測試素材是否可以：請 john 在 Discord 確認。
- [ ] 是否允許用其他 AI 寫程式：Discord 原文未取得。

## 待 john 決定

- （10/29 Claude）要不要用 GitHub Pages 放純靜態 demo 版（Codex T138 做好之後）？這會把 demo 紀錄公開放上網，repo 本來就要公開，Claude 建議可以，但要等 john 同意才開。

- T116 Codex：docs/API.md 尚無 T109 錄音轉寫／欄位抽取端點與來源驗證契約；目前按鈕停用「需要 Meta API」，不請求麥克風。逐欄編輯／確認元件已備妥，但端到端錄音送出待 Muse／Claude 提供契約後再接。

- T113 Codex：同步 POST /api/audits 不提供追蹤／計算分階段狀態；本次只呈現已知 upload bytes 與合併處理中。若要真實分階段進度，請 Claude 設計工作狀態端點；前端不以計時偽造階段。

- T105 Codex：先前本機瀏覽器 origin 授權被拒，本次不繞過；已補 390px 收縮與語意測試，但實際 viewport／鍵盤／螢幕閱讀器驗收仍需 Antigravity（T120）。

- Codex 10/28：本機 ffmpeg 缺 drawtext filter，pytest tests/scripts/test_gate_prepare.py::test_prepare_writes_sheet_and_blank_labels 失敗（其餘 75 pass）。請 Claude／Antigravity 確認具 drawtext 的 ffmpeg；本次不改後端／部署或跳過測試掩蓋。T89 npm 59 pass、build pass，但 pytest 全綠受此環境缺口阻擋。

- [Muse] 新套件 `meta-sam-parser`（Meta 官方、無依賴）：SAM 遮罩自研編碼，只能用官方解析器，已用於 track。requirements 請加 `openai` + `meta-sam-parser`。

- [Muse T107] SAM 覆蓋率分母 bug（需 Claude 修後端）：`audits.py` 用來源片格數（24fps）當分母，SAM 只出 15fps，天花板 62.5% 永遠低於門檻 0.8，所以 7 支全拒判。另 `by_t` 時間戳精確對齊在 15fps/24fps 混用下幾乎對不上，下游 events／鬼影也要修。Muse 不碰後端規則，等修好後重跑 T107 才有數字。

- [Muse] 主 checkout（~/Documents/slope-coach，切在 antigravity/T44-readme）有未解決的 `docs/STATUS.md` 衝突，`git pull origin main` 被擋下。Muse 沒碰它，在 worktree 照 origin/main 繼續做；請 Antigravity 或 john 解掉。

## 已做的決定

- 10/29 john：關卡三題通過後，主方向轉向「影片物理稽核」；斜坡教練保留為第二條路，只做維護。

| 日期 | 決定 | 原因 |
| --- | --- | --- |
| 10/28 | 競品結論（T21）：Tracker、FizziQ 已能讓一般人量影片中的 g；MotionPhys 已在研究用物理特徵偵測 AI 影片。所以我們不能說「第一個」，也不碰 AI 偵測。我們的差異要靠 Muse 自動做掉 Tracker、FizziQ 需要手動的步驟（選物體、選片段、說明結果），再加上凍結的品質門檻和拒判 | `docs/research/competitors.md` |
| 10/28 | 先驗證縮小版「影片物理稽核」，用上方關卡決定是否轉向；採用 award-strategy.md 的證據標準與拒判原則；不宣稱能辨識 AI 真偽 | john 選定。設計代理留作長期產品方向 |
| 10/28 | 評分權重：Impact 30%、Meta AI 工具運用 25%、技術深度 20%、Demo 25%；Indie 另看創意、技術野心、能不能運作 | 官方規則與 waiver |
| 10/28 | Muse 優先：產品裡的理解、判斷、說明都交給 Meta 模型；新開發任務優先給 Muse；畫面標明哪些由 Muse 產生 | john：要得名，主要得用 Muse |
| 10/28 | 拒判門檻（斜坡）：起滑後至少 6 個可用點；擬合殘差 RMS ≤ 10 mm；前 20% 路程至少 3 點才判斷初速度；差異門檻取 15% 和基準變異兩倍中較大者 | PLAN 第二十五節 |
| 10/28 | 下一次驗證的候選由 `physics/diagnose.py` 依數字產生，模型只能從中選擇並說明 | 模型不碰數字 |
| 10/27 | 產品內只呼叫 Meta 模型；所有測量數字由 `physics/` 計算 | 比賽規則；可重算、可檢查 |
| 10/27 | Muse Code 預設用 `muse-spark-1.3`，不用 Wonder 寫程式 | Wonder 的輸出很貴 |
| 10/29 | SAM 3.1 實際格式：Responses API（`input_text` 單一概念 + `input_video` 的 file_id，先 Files API 上傳），一行一影格，遮罩 base85 用官方解析器解框內柵格 | dev.meta.ai 文件 + 真片實測 |
| 10/29 | 官方價格（`meta_client/cost.py`）：Spark 標準 1.25/0.15/4.25，contributor 0.10/0.002/0.20；Wonder 4.00/0.20/20.00；SAM 影片每千格 0.20（每次至少 50 格）；語音每小時 0.18。未定價模型拒絕呼叫 | dev.meta.ai/pricing |
| 10/29 | `track_object` 回正規化座標（API v0.5）：質心 0..1、面積佔畫面比例；SAM 固定轉 15fps，缺格標 missing；審計端後端換算回 480 寬 | 後端 T84 契約 |
| 10/29 | Meta API 實際不強制執行 json_schema strict：同一提示詞三次回傳三種形狀（缺 key 改名、裸 array）。本機驗證是唯一防線：信封寬鬆（接受 object/array、question 別名）、內容嚴格（欄位、字數、check）。所有 Spark 函式提示詞加註確切 key 名 | T66 真打三次失敗換來的教訓 |
| 10/29 | T45/T67 槽位寫法：模型只寫 `{check_key}`/`{nearest_body}` 位置，不寫數字。`{nearest_body}` 是字串槽，程式先代換再跑 fill_numbers；填充後再過 check_model_text，數字 allowlist 含確定性捨入值（顯示捨入不該失敗）；insufficient_data 或無重力數字直接回 None、不呼叫 API | fill_numbers 只收數字；T67 spec |

## 成本紀錄（Meta API）

上限：額度 150 美元；後端硬上限 120 美元。每天收工前填。

| 日期 | 項目 | 花費（美元） | 累計 |
| --- | --- | --- | --- |
| 10/29 | T38：SAM 追蹤 Manus 籃球片（75 格，65 格命中） | 0.015 | 0.015 |
| 10/29 | T66：Spark 偵訊實測＋除錯（含 5 次失敗嘗試） | 0.075 | 0.090 |
| 10/29 | T107：SAM 重跑 7 支（6 meta＋1 manus，每支 $0.010–0.014） | 0.077 | 0.167 |

## 工作日誌（最新在上）

- 10/29 Muse 完成 T107（分支 muse/T107-sam-rerun）：audit_batch 跑 data/gate/clips 7 支，track_source 全是 sam，但 7 支全因「只追到 61–63%」拒判——查出是後端覆蓋率分母用 24fps 來源格數、SAM 只出 15fps（天花板 62.5% < 門檻 0.8），修法在後端已寫進待 john 決定。SAM 對照表和兩版比較已貼進關卡結果。花費 $0.077，累計 $0.167。pip install 用「逐一確認 requirements 可 import＋ffmpeg＋meta-sam-parser 存在」代替（venv 本來就齊，避免重裝弄壞環境）。
- 10/29 09:00 Claude：查出昨晚工具停下來的原因。(1) 各工具把當時看到的任務做完就結束了，Claude 後來加的任務沒有人去讀。(2) Muse 的 T107 要用 `/mnt/project-files/gate/`，但那個路徑只在 Claude 的雲端電腦上，Muse 早就回報找不到。已把生成影片放進 `data/gate/clips/`（T144），`audit_batch` 預設讀那裡，找不到的影片列為 missing，T107 也改成一步一步的指令。頂端加了「做完一件不要結束對話」。
- 10/29 06:40 Claude：巡查時發現 04:37 之後沒有任何工具 push 新東西（john 睡了，工具可能停了）。Claude 代做 T02。**Antigravity 下一件改成 T52（CI）**。
- 10/29 04:45 Claude：合併 Codex T133–T142（PR #51，npm 76、build 通過、主 bundle 64 kB）。做了 T143：說明和標題可以由 Muse Spark 寫，但要通過後端檢查才用。給 Muse 加 T112（在 MetaHooks 接上），給 Codex 加 T143、T145、T146、T149、T150、T151。Antigravity 到現在什麼都沒推，可能也是 GitHub 登入的問題，已在頂端寫明現在能 push。
- 10/29 04:10 Claude：Muse 的程式一直沒上 GitHub，原因是 Mac 上沒有 GitHub 登入；john 已用 `gh auth login` 設好，**以後 Muse 可以自己 push**。審查並合併 `muse/T67-headline`（T05、T29、T34、T38、T39、T28、T11、T24、T16、T45、T46、T47、T66、T67）。沒有金鑰外洩、不呼叫非 Meta 模型、數字都用槽位由程式填入、120 美元上限有實作。Claude 的雲端環境沒裝 `meta-sam-parser`，所以 test_sam 有 3 個測試失敗；john 的 Mac 上有裝，那邊會通過。
- 10/29 04:00 Claude：審查並合併 Codex PR #46（T100–T118 全部完成：結果牆、鬼影播放、重力刻度尺、並排比較、列印版、自動導覽等）。pytest 79、npm 69、build 通過，沒有禁用字。替 Codex 補 T133–T140。
- 10/29 03:50 Claude：Manus 交了 T23、T95、T123–T126（john 轉交），檢查後入庫。Claude 也完成了 T128（更多顏色）。Manus 的待辦清空；下一輪等 Muse 接上 SAM 後再更新 demo 稿。
- 10/29 03:40 Claude：john 去睡覺前要求給一整晚的量。新增 Muse T107–T111、Codex T113–T118、Antigravity T119–T122、Manus T123–T126、Claude T127–T131，並重寫頂端的順序表。
- 10/29 03:30 Claude：合併 Codex PR #42（T89、T90、T92）。新增生成影片的 demo 紀錄（T106），替 Codex 補 T101 到 T105。
- 10/29 03:35 Claude T99：稽核結果加上用一般人的話寫的說明（固定模板，API v0.7），新增 Codex T100。
- 10/29 03:25 Claude T98：網站判定結果表 `data/gate/product_results.md`。
- 10/29 Muse 完成 T45＋T67（commit 5c4d8a7、bacce3f，分支 muse/T45-fill、muse/T67-headline）：T45 稽核代理理由改 rationale_template＋{check_key} 槽位、fill_numbers 填入後再 check；T67 `headline.write_headline` 寫一句物理標題模板，{nearest_body} 程式代換、數字槽填入、禁真/假/AI 字，insufficient_data 回 None 不花錢。pytest 185 通過（gate_prepare 仍是原生失敗）。Muse 完成表全部打勾；push 仍無認證，待 john 手動推 muse/T38-sam-norm、muse/T66-interview、muse/T45-fill、muse/T67-headline。
- 10/29 Muse 完成 T66（commit 20f4337，分支 muse/T66-interview）：`interview.interview_audit` 抽 3 格問最多 3 題，驗證鏡像後端 checked_interview。真打發現 API 不強制 schema（三種形狀輪流出），已改寬鬆信封+嚴格內容+question 別名；實測 3 題（slow_motion/assumed_model/object_size_m）全過，約 $0.008/次。pytest 180 通過（gate_prepare 仍是原生失敗）。累計花費 $0.09。

- 10/29 Muse 完成 T38 新版（commit b696c68，分支 muse/T38-sam-norm）：整批舊工作搬上轉向後 main，`track_object` 改正規化座標（API v0.5），Manus 籃球片真打 SAM：75 格 65 中、軌跡左右/上下走向正確、$0.015。pytest 175 通過（1 個 gate_prepare 失敗是 main 原生環境問題，已驗證）。舊 11 分支作廢（基底太舊），改併新線。
- 10/29 Muse：push 仍無認證（11 條舊分支重試全滅），待 john 手動。官方 4 支 T38 測試片（/mnt/…）本機沒有，只測了 Manus 籃球片。

- 10/29 03:15 Claude：依 john 的決定改寫 AGENTS.md（目前方向、專案說明）與本檔頂端的分工表，新增 T92、T95、T96、T97。
- 10/29 03:10 Claude：關卡正式結果三題都通過。依決定規則應轉向「影片物理稽核」，已請 john 決定。
- 10/29 02:35 Muse 查證：Meta Model API 的 `/v1/models` 只有 muse-spark、muse-wonder-1.0、sam-3.1、muse-voice-transcribe-1.0、muse-image-1.0，**沒有影片生成**。關卡用的生成影片改由 john 在 Meta AI app／meta.ai 手動生成（提示詞在 `/mnt/project-files/gate/meta_ai_prompts.md`）。
- 10/29 02:40 例行巡查：Muse、Antigravity 仍然沒有 push；Codex 沒有新分支。Claude 加了真實影片的 demo 紀錄（T91），替 Codex 補 T89、T90。
- 10/29 Claude T88：網站稽核接上顏色追蹤（`track_source: color`）。為了不讓前端拒收新值，Claude 直接改了前端 4 個檔案的型別和標籤（只加一個值，沒動樣式），請 Codex 之後檢查。
- 10/29 02:35 Claude：john 確認時間窗和 track_ok，關卡 Q1 通過、Q3 通過，Q2 等 Meta AI 影片。
- 10/29 02:30 Claude：john 量到球直徑 0.11 m。關卡試跑：own_1 g = 9.62、own_2 g = 9.82 一致，own_3 g = 8.17 小幅不一致。舊版 frame_diff 三支都失敗。結果寫進「關卡結果」。
- 10/29 Claude：合併 Codex PR #32（T85、T86）。完成 T87 顏色追蹤，記進規則變更紀錄。真實影片上的追蹤已經正確，但用 5 公分算出的 g 只有一半左右，請 john 量球的直徑並確認時間標註。
- 10/28 02:05Z Claude 巡查：Codex 完成 11 件（PR #16，已審查合併）；Muse 和 Antigravity 還沒有 push。替 Codex 補了 T59 到 T63。
- 10/27 Codex T48：介面英/繁中切換，首次預設英文、記住語言偏好，所有頁面顯示層使用同一詞表；後端原始原因/使用者資料與數字不改寫。32 項測試、build 通過。

- 10/27 Codex T17：限時內完成預測影片疊加元件與原點/時間/缺失處理測試。只做契約指定的顯示座標映射，不重擬合；到終點停止，非 ok 或時間不近的觀測隱藏。無可核對真片，預設關閉並要求使用者核對；不宣稱實際對齊精度。30 項測試與 build 通過。

- 10/27 Codex T41：三種 verdict、原因/限制/原值呈現、禁止來源真假宣稱、multipart 時間窗與尺寸不臆測的測試完成；26 項 npm test 與 build 通過。

- 10/27 Codex T40：新增檢查影片頁與 AuditOut 型別，時間窗/尺寸/鏡頭確認以 multipart 送 /api/audits，顯示三種模型相對結果、原因、原始數字、疊加、散點、事件與限制；保留斜坡流程。22 項測試與 build 通過；不在前端計算測量值。

- 10/28 john 要求加更多任務。新增 T45 到 T58，重點放在：Muse 當稽核代理（提高 Meta 工具運用分）、英文介面與 demo 模式（評審體驗）、CI 與效能（能不能運作）、透視與單擺（技術深度）。
- 10/28 Claude 完成 T37 稽核端點（另開 `backend/audits.py` router，避免和 Muse 改 main.py 衝突；影片處理移到 `backend/video.py`）。完成表補到夠做一整晚：Muse 加 T38、T39、T16，Codex 加 T40、T41、T13b，Antigravity 加 T42 到 T44。
- 10/28 john 指定 Claude 為協調者。新增「完成表」，並在 AGENTS.md 加上自動接續規則。Muse 回報 T05 和 T29 已在本機完成（91 個測試通過），但還沒 commit：Muse 請照新規則 commit 並 push `muse/T05-meta-client`。
- 10/28 Claude 完成 T35：彈跳檢查（反彈比前一次高超過 5% 就判不一致）與物體持續性事件（中途消失超過 2 格、面積偏離中位數 2 倍、位移超過中位步長 4 倍）。這兩項不加進 10/29 的關卡，避免看到資料後才改規則。
- 10/28 Claude 把所有資料整合進本檔（原本的 docs/GATE.md 已併入「可行性關卡」），並加上「現在每個工具要做什麼」。
- 10/28 john 決定先驗證縮小版「影片物理稽核」。Claude 寫了關卡工具：`scripts/gate_run.py` 和疊加圖，規則先凍結，合成影片測試通過（PR #7、#8）。
- 10/28 john 拍了第一支測試影片，問題列在「缺什麼」。Claude 完成 T31 拋體檢查和 `scripts/flight_probe.py`。
- 10/28 Claude 完成 T30（`/media`），並審查 Codex PR #4：測試和 build 都通過，衝突已解。
- 10/28 Claude 完成 T15 與 `scripts/seed_demo.py`、T12、T26、T07、T06。
- 10/27 建立 AGENTS.md、CLAUDE.md、STATUS.md 初版。

- 10/27 Codex T50：新增稽核 JSON 保存與離線讀取，驗證 free_flight schema／有限數字／5 MB 上限；重播明示沒有新分析，禁止載入遠端影片與疊加圖。沒有捏造產品示範結果，需先保存真實 API 結果；36 項 npm 測試與 build 通過。

- 10/27 Codex T51：窄螢幕欄位／導覽換行、44px 控制目標、焦點外框、跳至工作區、強制色彩支援；曲線保留虛線 vs 實線圓點，新增鍵盤可讀資料表。npm 37 pass、build pass；pytest 53 pass/5 skip（缺 ffmpeg 等環境條件）。本機瀏覽器 origin 授權被拒，未繞過，實機手機／螢幕閱讀器驗收仍待 Antigravity。

- 10/27 Codex 工作總結：已依完成表完成並分支推送 T36a/T36b/T36c/T40/T41/T13b/T17/T48/T49/T50/T51；重新 pull main 後沒有剩餘 Codex 未勾項。最終 npm 37 pass、build pass、pytest 53 pass/5 skip。尚待真實影片疊加對齊與手機／螢幕閱讀器實測；只改 frontend 與本 STATUS，未推 main。
- 10/28 02:10 Claude 完成 T58：關卡結果自動附上總表和三題判定；manifest 新增 `track_ok` 欄。john 回報 Muse、Antigravity 說做完了，但 GitHub 上沒有它們的分支，代表還沒 commit 和 push。

- 10/27 Codex T59：支援 free_flight／bounce 選擇與 multipart 送出，結果與離線 parser 依 assumed_model 顯示；rebound_ratio_k 原值保留。npm 38 pass、build pass。

- 10/27 Codex T60：以依時間排序的文字時間軸顯示三種事件，保留原始秒數與 detail；size_trend 拒判區呈現原值與二維品質限制，不把事件判成因果。npm 40 pass、build pass。

- 10/27 Codex T61：新增 #/audits/:id 直接讀取與結果連結，ID 編碼並僅 GET；換 ID 時清空舊結果，忽略過期請求。離線重播不顯示需連線的結果連結。npm 41 pass、build pass。

- 10/27 Codex T62：稽核使用原生 XHR upload bytes 進度，上傳完成後明示等待後端分析（無分析百分比）；不重送。404／422 加操作提示並完整保留後端 reason／數字；網路、逾時與中斷有明確提示。無新套件或 API 契約變更。npm 43 pass、build pass。

### Codex T63：前端 data-testid 清單（給 Antigravity）

- 導覽：`nav-home`、`nav-setup`、`nav-prediction`、`nav-analysis`、`nav-verification`、`nav-report`、`nav-audit`；首頁 `home-audit`、`home-coach`。
- 共用：`workspace`、`workspace-error`（發生錯誤時）。
- 斜坡主要操作：`experiment-create`、`experiment-load`、`calibration-save`、`baseline-create`、`prediction-lock`、`trial-upload`、`trial-track`、`detections-save`、`release-suggest`、`release-confirm`、`comparison-create`、`intervention-select`（每個候選一個）、`intervention-link`、`report-markdown`、`report-csv`；結果圖 `comparison-chart`。
- 稽核輸入：`audit-video-input`、`audit-model`、`audit-submit`、`audit-id`、`audit-load`、`audit-import-json`。
- 稽核狀態與結果：`audit-progress`（請求中）、`audit-error`（錯誤時）、`audit-result`、`audit-verdict`、`audit-events`、`audit-size-trend`（有 size_trend 的拒判結果）、`audit-export-json`、`audit-export-markdown`。
- ID 不隨語言切換；其餘欄位請用可見 label／role。沒有結果或未達操作前提的元件不會出現在 DOM。

- 10/27 Codex T63：主要斜坡與稽核操作、導覽、狀態與結果加入穩定 data-testid，清單見本檔；測試確認英／中文不變。npm 44 pass、build pass、pytest 53 pass/7 skip（ffmpeg 等環境依賴），尚未重做瀏覽器端到端驗收。T59–T63 均只改前端與 STATUS，沒有改後端契約或物理門檻。

- 10/28 02:30 合併 Codex PR #19（T59–T63），合併後才補做審查：pytest 61、npm 44、build 都通過，沒有違規字眼，前端沒有自己算物理。john 要求增加特色。Claude 完成 T69（鬼影軌跡、星球比喻、尺寸誤差穩健度），並新增特色任務：Codex 的 T64 鬼影對照、T65 物理名片，Muse 的 T66 Muse 偵訊、T67 名片標題，Antigravity 的 T68。
- 10/28 Claude 完成 T70：稽核支援單擺，新增 Codex T71（畫面加上單擺選項）。
- 10/28 02:35 例行巡查：Muse、Antigravity 仍沒有推任何分支；Codex 沒有新分支（T64、T65、T71 待做）。Claude 完成 T72。
- 10/28 03:00 Claude 完成 T73 合成測試資料。john 說繼續做，明天再檢查。

- 10/27 Codex T64：鬼影影片／散點對照、播放滑桿、最大同時刻像素差與跳轉、事件回放按鈕；只用後端 ghost_points，無資料不補造、不插值。離線仍禁遠端媒體；最大差只作顯示，不作判定。新增 testid ghost-review/ghost-video/ghost-scrubber/ghost-gap/event-seek。npm 45 pass、build pass。
- 10/27 Codex T71：單擺選項與使用者擺長 length_m（選填、正有限數），離線支援 pendulum；週期與推算擺長直接顯示後端原值。npm 46 pass、build pass；testid pendulum-length。
- 10/27 Codex T65：新增可下載 PNG 的物理名片，包含原始數字、星球比喻、尺寸穩健度警告、reason／limits、可讀取的後端縮圖；離線不取遠端縮圖。未有 T67 模型標題時明示待提供，沒有假稱 Muse 已產生文字。合成 JSON 的 synthetic 標記在結果與卡片保留。testid physics-card/physics-card-download；npm 48 pass、build pass，pytest 56 pass/8 skip。PNG 排版與影片同步仍需 Antigravity 瀏覽器實測。
- 10/28 04:35 例行巡查：審查並合併 Codex PR #24（T64 鬼影對照、T71 單擺選項、T65 物理名片）。pytest 64、npm 48、build 都通過，前端沒有自己算物理，畫面沒有違規字眼，合成資料有標明 SYNTHETIC。給 Codex 補上 T74 到 T77。Muse、Antigravity 還是沒有推任何分支。
- 10/28 04:50 Claude 完成 T78（Muse 偵訊的後端契約）。
- 10/28 06:35 例行巡查：沒有新的分支。Claude 完成 T79（關卡標註輔助）。
- 10/28 Codex T74：#demo 同頁展示一致／不一致／拒判，直接打包 data/demo 三份後端合成結果，不改數字；顯示 SYNTHETIC 與效能非實證提示，離線無 API／媒體請求，各卡包含鬼影與名片。npm 49 pass、build pass。
- 10/28 Codex T75：稽核數字／名片與差距顯示採文字四捨五入；極小非零值用科學記號，不顯示成零。數字原值仍存在 title 與 JSON／Markdown，資料本身不變。npm 50 pass、build pass。
- 10/28 Codex T76：彈跳比例長條圖依 k 排序，提供 1.0 虛線與可讀資料；明示後端會套用容差，前端圖表不另下判定。testid bounce-chart；npm 51 pass、build pass。
- 10/28 Codex T77：接上 /api/audit-drafts 與 draft_id 回答提交，來源 model／mock 分開標示。相機、慢動作、模型、時間都須使用者明確確認，未知尺寸留空；不由問題填入數字。single-use draft 成功後清除，404／連線不明時要求重新準備，不自動重送；一般稽核與偵訊互斥避免結果競爭。新增 testid interview-panel/interview-video/interview-prepare/interview-questions/interview-camera/interview-slow/interview-model/interview-submit。npm 53 pass、build pass。

- 10/28 Codex 工作總結：T74–T77 已完成並各自推送；重新 pull main 後沒有剩餘 Codex 未勾項。最終 npm 53 pass、build pass、pytest 56 pass/11 skip（環境依賴）。#demo 可離線看三種結果；Muse 偵訊用現有契約。瀏覽器端到端與 PNG 視覺驗收仍交 Antigravity，未推 main。
- 10/28 12:40 例行巡查：審查並合併 Codex PR #27（T74 三種結果並排、T75 數字格式、T76 彈跳圖、T77 Muse 偵訊面板）。pytest 67、npm 53、build 都通過，面板有標明問題來源（Muse Spark 或固定問題），合成資料有標明 SYNTHETIC。發現尺寸只顯示 1 位小數的問題，交給 T80。新增 Codex 的 T80 到 T82。Muse、Antigravity 仍然沒有推任何東西。
- 10/28 15:45 john 說等一下就去拍片。Claude 完成 T83（關卡工具試跑）和 T84（SAM 介面）。
- 10/28 Codex T80：尺寸／長度改為三位有效數字（0.0670、2.40、0.250），只改顯示字串，原始匯出不變。補極小尺寸測試；npm 54 pass、build pass。
- 10/28 Codex T81：Guided demo 依序導覽既有首頁→偵訊→合成結果鬼影→物理名片→三結果對照，Back／Next／Exit 可操作；英文說明不冒充模型輸出、不另造素材。testid guided-demo/guided-next。npm 55 pass、build pass；瀏覽器捲動驗收待補。
- 10/28 Codex T82：英文判定統一 with the assumed model，PNG 判定改英文；移除自有畫面的 fixture／real 與問題欄位代碼、縮短按鈕。SYNTHETIC、mock 來源仍明示；原始後端原因／問題／使用者文字不改寫。補英文呈現檢查；npm 56 pass、build pass。

- 10/28 Codex 工作總結：T80–T82 已完成並推送，PR #30 待審。再次 pull main 後沒有新增 Codex 未勾項。npm 56 pass、build pass、pytest 56 pass/13 skip（環境依賴）。導覽捲動與視覺驗收仍待 Antigravity；未推 main。
- 10/28 22:35 例行巡查：審查並合併 Codex PR #30（T80 有效數字、T81 demo 導覽、T82 英文文字）。pytest 69、npm 56、build 都通過，也有測試確認畫面沒有 real、fake、detect 等字眼。新增 Codex 的 T85、T86。Muse、Antigravity 仍然沒有推任何東西。
- 10/28 Codex T85：一般稽核／偵訊新增物體名稱（預設 ball），傳 object_name；結果、PNG、Markdown 標明 SAM 3.1 或 frame differencing（no model used），JSON 保留 track_source。testid audit-object-name/interview-object-name；npm 57 pass、build pass。
- 10/28 Codex T86：一般稽核加慢動作 yes/no/未提供，結果、PNG、Markdown 保留回答，JSON 原值不變；舊紀錄無欄位仍顯示未提供，不假定 false。slow_motion=true 的拒判突出顯示後端 reason 原文，不自行改數字或歸因。testid audit-slow-motion/audit-slow-answer/audit-timing-limit；npm 58 pass、build pass。

- 10/28 Codex 工作總結：T85／T86 已推送，PR #32 待審；pull main 後沒有新增 Codex 未勾項。npm 58 pass、build pass、pytest 56 pass/13 skip（環境依賴）。追蹤來源與慢動作回答全流程保留，未推 main；瀏覽器端到端待驗收。
- 10/28 Codex T89：審核 color 型別、離線 parser、來源與匯出標籤均保留；統一來源 badge 樣式，補英／繁中測試，明示未使用模型。npm 59 pass、build pass；pytest 結果見本次驗證，環境跳過項仍保留。
- 10/28 Codex T90：demo／導覽加入 john 三份實拍結果，兩份一致與一份原因不明的不一致全部呈現；標明 john 拍攝與確認標註。保留空 video_url，無公開住家影片；顯示已存軌跡、鬼影、原始數字。npm 60 pass、build pass；pytest 75 pass/1 fail，仍為已記錄的 drawtext 環境缺口。
- 10/28 Codex T92：空網址與未知路由預設開稽核，主分頁為 Check video／Experiment coach；首頁說明限定為與假設模型核對，保留 demo 導覽、範圍說明與全部斜坡子路由。testid nav-audit/nav-coach，舊 nav-setup 等仍在教練內。npm 60 pass、build pass；pytest 76 pass/1 fail（既有 ffmpeg 無 drawtext），未宣稱全綠。

- 10/28 Codex 工作總結：T89→T90→T92 已各自提交與推送，PR #42 待審；再次 pull main 後沒有 Codex 未勾項。前端 npm 60 pass、build pass；pytest 76 pass/1 fail，drawtext 缺口已列待 john 決定，不修改角色外的程式或掩蓋測試。未推 main。
- 10/28 Codex T100：結果最上方、PNG 與 Markdown 加 explanation 原文與 template/model 來源，不改數字；離線 parser 驗證。npm/build 通過；pytest 的 drawtext 環境缺口仍列待決定。
- 10/28 Codex T101：#wall 全列 real_own 與 generated 儲存結果，不挑片；來源、判定、說明、星球與追蹤標示、資料不足原因均顯示，無網路取片。npm/build 通過；pytest 全跑，drawtext 環境失敗仍待協調者處理。
- 10/28 Codex T102：無影片時可播放／暫停、拖曳後端 points 與 ghost_points，缺口不插值。時鐘只控制顯示，不算物理；testid points-play/points-scrubber。npm/build 通過；pytest drawtext 缺口維持紀錄。
- 10/28 Codex T103：新增對數重力刻度、五個固定參考星球、後端 g 與 low/high 範圍；缺正有限數不畫量測標記。文字替代與單測；npm/build 通過，pytest drawtext 環境缺口未變。
- 10/28 Codex T104：上傳區新增英／繁中六項拍攝檢查與拒判原則，不替使用者確認條件；testid capture-checklist。npm/build 通過；pytest drawtext 缺口已知。
- 10/28 Codex T105：390px 巢狀卡片收縮、長文字換行、range 控制與圖表文字替代補強；npm/build 通過。實際瀏覽器 viewport／鍵盤驗收受先前 origin 拒絕所限，已列待決定並交 Antigravity；不宣稱實測通過。pytest drawtext 失敗未隱藏。
- 10/28 Codex T113：上傳 bytes 百分比與伺服器追蹤／計算合併等待狀態，無假計時或階段百分比；錯誤仍保留後端 reason。真實階段端點缺口列待決定；npm/build 通過，pytest drawtext 已知失敗。
- 10/28 Codex T114：#compare 可選任意兩份紀錄，左右完整顯示說明、實測／鬼影、重力刻度與來源；小螢幕改上下，來源不作判定。npm/build 通過，pytest drawtext 已知失敗。
- 10/28 Codex T115：選定單筆稽核列印，A4 stylesheet 包含判定／說明／數字／軌跡／限制及來源，不列印其他頁面紀錄；保留全部內容不截斷。npm/build 通過，瀏覽器一頁視覺驗收仍待 Antigravity；pytest drawtext 已知失敗。
- 10/28 Codex T116：語音按鈕停用並標 Requires Meta API（沒有端點），不錄音；已提供轉寫文字與欄位編輯、逐欄勾選後才可送出的本地介面。契約缺口已列待決定，不虛構模型結果。npm/build 通過；pytest drawtext 缺口。
- 10/28 Codex T117：新結果牆、比較、列印與名片統一 assumed-model 英文判定，來源用可讀名稱；後端原文與數字不改寫。測試遍歷三模型三判定；npm/build 通過，pytest drawtext 環境缺口仍列明。
- 10/28 Codex T118：首頁可啟動 30 秒導覽，固定 own_2→meta_clip2→meta_clip4，各 10 秒、可暫停續播，只讀儲存結果。補三判定順序與全部 10 份結果 schema 測試；npm 69 pass、build pass；pytest 78 pass/1 fail（drawtext 已列待決定）。

- 10/28 Codex 工作總結：順序表 T100→T101→T102→T103→T104→T105→T113→T114→T115→T116→T117→T118 的前端實作已各分支提交，PR #46 待審；再次 pull main 無新增 Codex 待辦。npm 69 pass、build pass；pytest 78 pass/1 fail（ffmpeg drawtext 缺口）。T105 實際 viewport／鍵盤、T115 列印視覺驗收未完成；T113 細分階段 API、T116 語音 API 尚缺，按誠實降級實作並列待決定。未推 main。
- 10/29 Codex T133：一般稽核與偵訊共享本機影片預覽、兩個鍵盤可用時間把手與 0.01 秒輸入；必須確認時間窗才能送出，改界線／重選片即失效。不自動猜起終點。npm/build 通過；pytest drawtext 環境缺口仍列待決定。
- 10/29 Codex T142：接 POST draft/windows，候選以時間軸色塊與鍵盤按鈕顯示；選取只移把手，不自動確認。標示程式建議未使用模型，一般稽核重用該草稿送出，不重複傳影片。補端點測試，測試環境補既定 SDK。
- 10/29 Codex T136：稽核首頁加入指定三筆結果卡與一句話開場，點擊 #examples/key 開對應儲存證據，不把範例 key 當後端 ID。npm 72 pass、build pass；pytest 187 pass/4 fail（本機缺 meta-sam-parser、drawtext）。

- 10/29 Codex 測試環境：合併 Muse 後，已補專案既定 OpenAI SDK 到 /tmp 測試環境；pytest 仍有 3 項缺 meta-sam-parser、1 項 ffmpeg 無 drawtext。未改後端或跳過測試。
- 10/29 Codex T137：支援 /audit/id 與既有 hash 連結，GET 讀取與 404 友善錯誤；結果可複製 origin+編碼ID連結。部署需 SPA fallback 到 index.html，未部署或改伺服器。npm 73 pass、build pass；pytest 環境 4 項失敗保留。

- T138 靜態建置：在 repo 執行 `VITE_DEMO_ONLY=1 npm --prefix frontend run build`，輸出 frontend/dist。只打包 data/demo 紀錄，關閉上傳、教練後端操作與自動讀取；API 層亦拒絕所有網路呼叫。可用 `npm --prefix frontend run preview` 本機預覽；本次不公開部署。/audit/id 深連結仍需主機 SPA fallback。
- 10/29 Codex T138：VITE_DEMO_ONLY=1 建置只用保存紀錄，停用上傳與教練操作、抑制自動讀取；API 層 read/upload/XHR 全阻擋。分享 ID 僅查本地 catalog。標準／靜態 build 均通過，npm74 pass；完整 pytest4項環境失敗。build指令與SPA要求已寫STATUS。
- 10/29 Codex T135：#how 五步流程以 Meta model／deterministic code／user input 分清來源；可選紀錄查看實際 track_source、explanation.source。問答來源未保存在紀錄時明示未知，不宣稱已啟用模型。npm/build 通過；pytest4項環境失敗。
- 10/29 Codex T140：七個結果元件在三模型下遍歷空 points、稀疏 numbers、缺 explanation、nearest_body=null；不崩潰、不產生 NaN／假數字、不修改輸入。npm76 pass、build pass；完整 pytest4項環境失敗。
- 10/29 Codex T139：大頁面與範例資料按需載入，React 共用chunk可快取。production entry 64,514 bytes（gzip前），React另222.29 kB；原主入口約426.87 kB。靜態entry64,182 bytes。build加入250000bytes自動門檻；npm76 pass，標準／demo build pass，pytest187 pass/4 fail（本機缺SAM解碼套件與drawtext）。

- 10/29 Codex 工作總結：T133→T142→T136→T137→T138→T135→T140→T139 已各分支完成並推送；最新 pull 無 Codex 未勾項。最終 npm76 pass，標準 build entry64,514bytes、demo build entry64,182bytes（均gzip前），React另222.29kB。範例強制 replay，靜態模式不取後端媒體。依 Muse 已合併的需求在 /tmp 測試環境安裝 meta-sam-parser 後 SAM 三測試通過，完整 pytest190 pass/1 fail，只剩 ffmpeg缺drawtext；未略過測試、不改後端。未公開部署、瀏覽器視覺驗收仍待 Antigravity。
