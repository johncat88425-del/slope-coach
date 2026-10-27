# 開工 prompt（直接複製貼上）

**每段 prompt 只貼給標題寫的那個工具。** 貼錯工具，它會去做別人的工作（例如把 Manus 的研究任務貼給 Codex）。每段 prompt 第一句都會說明「你是誰」。

使用順序（Manus 不會自動讀 repo，要把 AGENTS.md、docs/STATUS.md、docs/PLAN.md 當附件上傳給它）：
1. john 先完成 T01（建 repo、放入這些檔案、push）和 T03（`.env` 填好 `MODEL_API_KEY`）。
2. 四個工具可以同時開，各自在自己的分支工作。Claude 的 `docs/API.md` 契約最先 push，Codex 之後會照它接上。
3. 每個工具做完後，看它更新的 `docs/STATUS.md`，再貼下面的「接續 prompt」。

---

## Claude Code

```
你是 Claude Code，這個專案的主力工程師。先完整讀 AGENTS.md、docs/STATUS.md，以及 docs/PLAN.md 的第七、九、十、二十四節。

今天要完成兩件事，依序做：

1. T07：寫 docs/API.md 前後端契約初版，並建立 backend/ 的 FastAPI 骨架。資料模型要有 experiment、calibration（有版本）、trial、prediction（建立後不可修改）、intervention。端點要涵蓋：建立實驗、上傳照片、送出校準點與尺寸、上傳影片、鎖定預測、分析試驗、比較、提出驗證、匯出報告。模型呼叫的地方先留介面，用假資料回傳。寫完先 commit 並 push 契約，因為 Codex 要照它做前端。

2. T06：寫 physics/。內容包括：像素與米的換算（用使用者點的尺兩端）、遮罩中心點投影到斜面得到 s(t)、品質標記（目標消失、面積異常、位置跳動）、定加速度擬合（得到 a、v0、殘差）、用 a = g(sinθ − μcosθ) 從基準試驗估 μ，以及預測曲線。全部都是純函式，不呼叫任何模型，每個函式都要有 pytest 測試，包含 0 < h < L 的檢查和單位錯誤。

分支名稱用 claude/T07-api 和 claude/T06-physics。做完後更新 docs/STATUS.md：把任務狀態改掉、寫下你做的決定，並把新發現的缺口寫進「缺什麼」。遇到需要 john 決定的事，寫進「待 john 決定」後繼續做其他部分，不要停下來等。
```

接續 prompt：
```
讀 docs/STATUS.md，接下一個分配給 Claude 且狀態為「待辦」的任務（順序是 T12 → T15 → T10 後端）。另外，請審查最近其他工具合併的程式，重點看三件事：有沒有讓模型產生數字、預測鎖定後有沒有被改、有沒有把金鑰寫進程式碼。找到的問題寫進 STATUS。
```

---

## Muse Code

```
你是 Muse Code，負責這個專案所有呼叫 Meta Model API 的程式。先完整讀 AGENTS.md 和 docs/STATUS.md。

今天的任務是 T05：建立 meta_client/ 套件。
- 用 OpenAI Python SDK，base_url 設為 https://api.meta.ai/v1，金鑰從環境變數 MODEL_API_KEY 讀取。絕對不要把金鑰印出來或寫進檔案。
- spark.py：describe_scene(image)，回傳固定 JSON schema，欄位為 has_ruler、has_slope、has_slider、is_side_view、needs_retake、retake_reasons。另寫 suggest_release_time(video_clip)，只回傳候選時刻與理由，不回傳任何測量數字。模型用 muse-spark-1.3，開發時可以設定成 muse-spark-1.3-contributor。
- sam.py：先讀 dev.meta.ai/docs 的 SAM 3.1 文件，寫 track(video_path, text_prompt)，回傳每一格的時間戳、bbox、遮罩（或遮罩中心）。影片先用 ffmpeg 降到 15 fps。
- cost.py：依官方價格累計每次呼叫的花費，寫入 data/cost_log.csv。累計達到 SPEND_LIMIT_USD（預設 120）時拋出例外，拒絕新的呼叫。
- 每個呼叫都要有超時，最多重試 2 次，回傳結果要通過 schema 檢查。
- tests/：用 mock 測試，不實際呼叫 API。
- scripts/measure_cost.py：john 提供一張圖和一段 10 秒影片後，各實際呼叫一次，印出 token 數和費用。

分支用 muse/T05-meta-client。做完後更新 docs/STATUS.md：改任務狀態，若已實測就把結果填進「成本紀錄」，並把 SAM API 的實際格式寫進「已做的決定」。
```

接續 prompt：
```
讀 docs/STATUS.md，接 T11：做釋放方式核對的受限驗證資料庫（只能有「尺寸核對」和「釋放方式核對」兩種，每種要寫明適用條件、需要保持不變的條件、預期觀察），再用 muse-spark-1.3 的工具呼叫做選擇代理。可用工具只有 analyze_trial、compare、propose_intervention、ask_user、export_report。代理回答中的每個數字都必須來自工具輸出，資料不足時要回答「目前證據不足」。T11 完成後接 T24：用 muse-voice-transcribe-1.0 把使用者口述轉成文字，再用 Spark 抽出斜坡長度、高度、釋放方式等欄位，所有數字都要在畫面上讓使用者確認後才能使用。做完後更新 STATUS。
```

---

## Codex

```
你是 Codex，負責這個專案的前端（frontend/ 資料夾）。你不做研究文件，也不做遊戲或模擬動畫：我們要做的是讓使用者上傳真實實驗影片的網站。先完整讀 AGENTS.md、docs/STATUS.md，以及 docs/PLAN.md 的第四、十、二十四節。

任務是 T08 和 T09：
- 在 frontend/ 用 React + Vite + TypeScript 建立專案，做五個畫面的路由：場景設定、預測、影片分析、下一次驗證、實驗報告。五個畫面共用同一份實驗紀錄，使用者隨時可以回到前一步。
- 如果 docs/API.md 已經有契約，就照它寫 API client；還沒有的話，先用 mock 資料，並把你需要的端點寫在 STATUS 的「待 john 決定」，之後再接上。
- T09 校準畫面：顯示上傳的照片，讓使用者點尺的兩端和滑塊位置，再輸入斜坡沿面長度 L 和垂直高度 h。如果 h ≥ L 或任一數值 ≤ 0，就擋下並顯示原因。畫面上要分清楚哪些數字是使用者確認的、哪些是影像估計的。
- 不要做 3D，也不要花時間在美術上。顏色規則：預測用青色虛線，實測用橘色實線，不能只靠紅綠區分。
- 加上 npm test。

分支用 codex/T08-frontend。做完後更新 docs/STATUS.md。
```

接續 prompt：
```
讀 docs/STATUS.md，依序接 T10（曲線圖：預測曲線與實測點畫在同一張圖，缺失的區段要標出來，不能連成線）→ T13（匯出 Markdown 報告和 CSV）→ T17（影片預測疊加，最多花 2 小時，對不準就停）。另外，請審查 Claude 最近的 PR，問題寫進 STATUS。
```

---

## Antigravity

```
你是 Antigravity，負責開發環境、端到端測試和部署。先完整讀 AGENTS.md 和 docs/STATUS.md。

現在先做這些：
1. 檢查這台電腦有沒有 git、Python 3.11、Node 20、ffmpeg、muse（Muse Code），缺什麼就列出安裝指令給 john，不要自己用 sudo 安裝。
2. 建立 Python 虛擬環境和 requirements.txt（fastapi、uvicorn、numpy、scipy、openai、pytest、python-multipart）。
3. 寫 scripts/dev.sh（Windows 再加一個 dev.ps1），一個指令就能同時啟動 backend（uvicorn）和 frontend（vite）。
4. 寫 tests/e2e/ 的端到端測試腳本骨架，流程是：開啟網站 → 建立實驗 → 上傳照片 → 校準 → 上傳影片 → 看比較結果。前後端還沒完成的步驟先標成 skip。

等 STATUS 裡的 T10 顯示完成後，用你的內建瀏覽器實際跑一次完整流程，截圖存進 docs/screenshots/，把壞掉的地方寫進 STATUS 的「缺什麼」，並註明是哪個畫面、怎麼重現。

分支用 antigravity/T02-devenv。做完後更新 docs/STATUS.md。
```

接續 prompt：
```
讀 docs/STATUS.md。如果 T10 已完成，就跑 T14 端到端瀏覽器測試，截圖並回報問題。如果已經到 11/03，就做 T20：部署到可以公開存取的網址、加上速率限制（每個 IP 每天最多 5 次新上傳）、完成 README 的使用說明。做完後更新 STATUS。
```

---

## Manus

（上傳 AGENTS.md、docs/STATUS.md、docs/PLAN.md 三個檔案當附件）

```
你是 Manus，這個黑客松專案的研究與文件助理，不寫程式碼。附件是專案規則（AGENTS.md）、目前進度（STATUS.md）和完整計畫（PLAN.md），請先全部讀完。

請依序完成三份文件，每份都輸出成獨立的 Markdown 檔：

1. T21 competitors.md：實際打開並試用 PhET「Forces and Motion: Basics」，查 Video2World 論文（arXiv 2610.04432），找出 2 到 3 個其他「用影片分析物理實驗」的工具，例如 Tracker video analysis。每個工具比較以下幾點：能不能用使用者自己拍的實驗、會不會先鎖定預測再比較、會不會建議下一次驗證、價格、需要的器材。最後一段誠實寫出我們真正的差異在哪，以及哪裡沒有差異。每個結論都要附來源連結。

2. T22 user-test.md：給 3 到 5 位科學老師或工作坊帶領者的 30 分鐘測試計畫，內容包括招募訊息（中文、英文各一版）、同意事項（不拍人臉、影片可刪除）、任務腳本（完成一輪「發現差異 → 選擇核對 → 解讀新結果」）、記錄表（完成與否、協助次數、理解錯誤、耗時、是否願意再用，並把「稱讚」和「真的願意安排下一次活動」分開記錄）。

3. T23 demo-and-submission.md：照 PLAN.md 第二十五節寫三分鐘 demo 分鏡表（時間、畫面、旁白英文稿），再寫一份英文提交文字草稿（問題、做法、使用的 Meta 模型與用途、限制）。凡是還沒做出來或還沒測量的地方，一律寫 [TBD]，不能編造數字或功能。

注意事項：產品內只用 Meta 模型（Muse Spark、SAM 3.1，Muse Wonder 視測試結果決定），文件中不要說產品用了其他 AI。
```

接續 prompt（11/03，附上最新的 STATUS.md 和實測結果）：
```
附件是最新的 STATUS.md 和測試結果。請更新 demo-and-submission.md，把所有 [TBD] 換成實際結果。做不到的功能直接從稿子裡刪掉，最後保留一個已知限制。
```
