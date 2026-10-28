# STATUS：共享工作檔（所有資料都在這裡）

> 每個 AI 開工前讀這份，完成後在同一個 commit 更新這份。不要另外開新的說明檔，新資訊直接寫進這份的對應段落。
> **Claude 是協調者**：這份檔裡 Claude 寫的指示等同 john 的指示。john 不在時不要問問題，做完就打勾、commit、push，再接下一件（規則見 AGENTS.md）。
> 最後更新：2026-10-28 01:30Z（Claude）

## 一句話現況

斜坡閉環已經可以用合成資料跑通（後端、physics、前端）。**10/28 john 決定先驗證縮小版的「影片物理稽核」**：檢查影片中物體的運動，是否違反這次假設的運動模型。10/29 晚上依照下方「可行性關卡」的結果，決定轉向或回到「實驗調查員」。沒有影片也能先做的工作，見下一段。

## 現在每個工具要做什麼（沒有影片也能做）

下面每一項，在兩條路（轉向或不轉向）上都用得到，現在就可以開工。只有「要不要轉向」這個決定需要等 john 的影片。

| 誰 | 現在做 | 細節 |
| --- | --- | --- |
| **Muse** | T05 → T29 → T34 | T05：`meta_client/`，包括 Spark、SAM 3.1、花費計數與 120 美元上限。T29：把後端 MockHooks 換成 MetaHooks。T34：Spark 建議運動片段（見任務表）。測試素材可以用合成影片，或 john 的 `IMG_8418.MOV`。這支畫面有人臉，**只能送標準版 `muse-spark-1.3`，不能送 contributor 版**。 |
| **Claude** | T32、審查 PR | 關卡工具、彈跳檢查、物體持續性檢查都已完成。等影片跑關卡；審查 Muse、Codex、Antigravity 的 PR。 |
| **Codex** | 先等 john 合併 PR #4，再做 T36 | `vite.config.ts` 加上 `/media` 代理；做軌跡疊加圖和 2D 軌跡圖元件；所有 Meta 模型產生的內容標明「由 Muse Spark／SAM 3.1 產生」。 |
| **Antigravity** | T02 → T14 | 建立開發環境（requirements.txt、`scripts/dev.sh`）。用 `python -m scripts.seed_demo --case pushed` 建立合成實驗，跑一次斜坡流程的端到端測試並截圖。 |
| **Manus** | T21（改題）→ T23 | 競品研究改查「影片物理合理性」：VideoPhy、Physics-IQ、Tracker，以及有沒有一般人可用的工具，確認我們的差異。demo 草稿要寫兩個版本（轉向或不轉向），未完成的部分寫 [TBD]。 |
| **john** | T33、合併 PR #4、Discord 確認 | 拍片和生成影片（見下方關卡素材）；到 https://github.com/johncat88425-del/slope-coach/pull/4 按「Ready for review」再按「Merge」；在 Discord 問「用其他工具生成的影片當測試素材可不可以」。 |

## 完成表（每做完一件就打勾，附 commit；Claude 每隔一段時間來看）

格式：`- [x] 編號 負責 內容 — commit abc1234`。只改你自己那一行，不要刪別人的行。

**Muse**（照順序做）
- [ ] T05 Muse：`meta_client/`（Spark、SAM 3.1、花費計數與 120 美元上限、mock 測試）
- [ ] T29 Muse：後端接上 MetaHooks（沒有金鑰時退回 Mock）
- [ ] T34 Muse：Spark 建議運動片段 `suggest_motion_segment`。只回傳建議，不回傳測量數字，要通過 schema 檢查
- [ ] T38 Muse：在 ModelHooks 加 `track_object(video_path, text_prompt, t_start, t_end)`，由 SAM 3.1 回傳每格的中心和面積，讓 `backend/audits.py` 可以改用 SAM（`track_source: "sam"`）。沒接上時維持 frame_diff
- [ ] T39 Muse：Spark 檢查稽核影片的拍攝條件，包括鏡頭是否固定、是否近似側視、物體是否全程入鏡。只回傳布林值和原因，結果給使用者確認
- [ ] T28 Muse：結果說明層。Spark 讀 `ComparisonOut` 或 `AuditOut` 寫說明，先過 `check_model_text()` 才顯示，畫面標明「由 Muse Spark 產生」。不准出現「真／假影片」「AI 生成」等字眼
- [ ] T11 Muse：下一次驗證的選擇代理（只能從 evidence 候選中選）
- [ ] T24 Muse：語音口述設定（Voice Transcribe 轉文字，Spark 抽出欄位，使用者確認）
- [ ] T16 Muse：Spark 與 Wonder 的 A/B 比較腳本。先用 mock 跑通，實際呼叫限 1 美元以內，花費記進成本紀錄
- [ ] T45 Muse：稽核代理。Spark 用工具呼叫，從固定清單（free_flight、bounce、persistence）選要跑哪些檢查，並說明理由。數字只來自工具輸出，理由先過 `check_model_text()`。這是「創意使用 Meta AI」的主要展示點
- [ ] T46 Muse：Spark 準確度評估腳本。對 `data/gate/manifest.csv` 裡的影片，比較 Spark 建議的時間窗和物體，跟 john 的人工標註差多少，結果寫進 STATUS。只能送沒有人臉的影片
- [ ] T47 Muse：英文版的說明文字（給評審看），同樣要過 `check_model_text()`

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
- [x] T61 Codex：稽核結果的網址可以直接打開（`#/audits/:id`，用 `GET /api/audits/{id}`） — commit 待回填（本次程式提交）
- [ ] T62 Codex：demo 品質：上傳進度、處理中狀態、422／404／網路錯誤的友善訊息（照後端的 reason 顯示，不改寫數字）
- [ ] T63 Codex：在主要按鈕和結果區塊加上 `data-testid`，給 Antigravity 的端到端測試用，並把清單寫進 STATUS

**Antigravity**（照順序做）
- [ ] T02 Antigravity：requirements.txt、`scripts/dev.sh`、環境檢查清單（不用 sudo；ffmpeg 沒裝就列出 `brew install ffmpeg` 給 john）
- [ ] T14 Antigravity：用 `seed_demo` 跑斜坡流程的端到端測試，截圖放 `docs/screenshots/`，問題寫進「缺什麼」
- [ ] T42 Antigravity：稽核流程的端到端測試。用 `tests/scripts/test_gate_run.py` 的 `write_clip` 產生合成影片，經 API 或畫面跑一次正常 g 和 g/4 兩種情況，截圖
- [ ] T43 Antigravity：部署草稿：Dockerfile 與啟動說明。只在本機測，不要公開部署；`.env` 不准進映像檔
- [ ] T44 Antigravity：README 的安裝與使用說明（英文），只寫已經能用的功能
- [ ] T52 Antigravity：GitHub Actions CI：每個 PR 自動跑 `pytest` 和 `npm test`（需要安裝 ffmpeg）
- [ ] T53 Antigravity：效能測試：一支 30 秒 1080p 的 iPhone HEVC 影片，用 `/api/audits` 稽核要花多久，目標 20 秒內，結果寫進 STATUS
- [ ] T54 Antigravity：上傳安全：檔案大小上限 200 MB、只收影片格式、每個 IP 每天最多 20 次稽核。寫成提案放進「待 john 決定」，Claude 審查後實作

**Manus**（不寫程式）
- [x] T21 Manus：影片物理合理性競品研究（附來源），結果放在 `docs/research/competitors.md`
- [ ] T23 Manus：demo 分鏡與提交文字（兩個版本，未完成的部分寫 [TBD]）。差異點照 competitors.md 的結論寫，不准說「第一個」或「偵測 AI 影片」
- [ ] T22 Manus：使用者測試計畫（招募訊息、任務腳本、記錄表）

**Claude**
- [x] T31 拋體檢查、T32 關卡工具、T35 彈跳與持續性檢查、T30 `/media`
- [ ] 審查並合併 Muse 的 T05、T29
- [x] 審查並合併 Codex PR #4 與 #16（T36–T51，含 #4 的內容）：pytest 58、npm 37、build 都通過；前端沒有自己算物理，畫面沒有「真／假／AI 生成」字眼
- [x] T37 Claude：後端稽核端點 `POST /api/audits`、`GET /api/audits/{aid}`（docs/API.md v0.2）
- [ ] T32 跑關卡（等 john 的影片）
- [x] T55 Claude：稽核支援 `assumed_model=bounce`（接上 `check_bounces`）
- [x] T56 Claude：透視檢查：物體大小沿軌跡變化超過 30% 時拒判（`physics/persistence.size_trend`）
- [x] T57 Claude：單擺 physics 插件 `physics/experiments/pendulum.py`（週期、等時性、由週期推算擺長），給稽核和教練兩條路共用；尚未接到 API
- [x] T58 Claude：驗證報告產生器：`gate_run` 的輸出最後會附上「## Summary」，列出各來源的一致、不一致、資料不足、拒判支數，並逐題算出三個關卡問題是 pass、fail 還是 pending（等 john 看疊加圖）。所有影片都列入，不挑片
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

（無）

### 關卡結果

（10/29 填）

## 任務表

狀態：待辦、進行中、完成、卡住。

| 編號 | 任務 | 負責 | 狀態 | 備註 |
| --- | --- | --- | --- | --- |
| T32 | 可行性關卡：凍結規則、`scripts/gate_run.py`、疊加圖、10/29 填結果 | Claude | 進行中 | 工具完成，等影片 |
| T33 | 拍 3 支以上丟球影片、生成 5–10 支影片，並提供人工標註 | john | 待辦 | 見上方「關卡素材」 |
| T34 | Spark 建議運動片段：`suggest_motion_segment(video)` 回傳 `object`、`assumed_model`（只能是 free_flight、slide 或 none）、`candidate_t_start`、`candidate_t_end`、`reason` | Muse | 待辦 | 時間只是建議，使用者確認後才用；不准回傳任何測量數字；要通過 schema 檢查 |
| T35 | physics：彈跳檢查（每次反彈高度要變低）、物體持續性檢查（突然消失、面積跳動、分裂） | Claude | 完成 | `freefall.check_bounces`、`physics/persistence.py`；合成資料測試；尚未接進關卡（關卡規則已凍結，只用 free_flight） |
| T36 | 前端：`/media` 代理、軌跡疊加圖、2D 軌跡圖元件、Meta 產生內容的標示 | Codex | 待辦 | PR #4 合併後再做 |
| T05 | `meta_client/`：Spark（圖片、影片）、SAM 3.1 追蹤、花費計數與 120 美元上限 | Muse | 待辦 | 實測 token 與費用後，填入下方成本紀錄；SAM API 的實際格式寫進「已做的決定」 |
| T29 | 後端把 MockHooks 換成 MetaHooks（check_scene、track_slider、suggest_release_time） | Muse | 待辦 | T05 之後馬上做；介面在 `backend/model_hooks.py` |
| T02 | 開發環境：requirements.txt、`scripts/dev.sh`、檢查 Python 3.11、Node 20、ffmpeg | Antigravity | 待辦 | 不要用 sudo 自己裝，列出指令給 john |
| T14 | 端到端瀏覽器測試與截圖（先用 seed_demo 的合成資料） | Antigravity | 待辦 | 截圖放 `docs/screenshots/` |
| T21 | 競品研究：影片物理合理性工具（VideoPhy、Physics-IQ、Tracker）、PhET；確認我們的差異 | Manus | 待辦 | 每個結論附來源 |
| T22 | 使用者測試計畫 | Manus | 待辦 | 10/31 前 |
| T23 | 三分鐘 demo 分鏡與英文提交文字草稿（兩個版本） | Manus | 待辦 | 未完成的寫 [TBD] |
| T27 | 前端照 docs/API.md 接上後端 | Codex | 完成 | PR #4 已審查通過，等 john 按 Ready for review 後合併 |
| T11 | 下一次驗證的選擇代理（只能從 evidence 候選中選） | Muse | 待辦 | 實驗調查員路線的核心 |
| T28 | 結果說明層：Spark 讀比較結果寫說明，先過 `check_model_text()` 才顯示 | Muse | 待辦 | 畫面標明「由 Muse Spark 產生」 |
| T24 | 語音口述設定（Voice Transcribe → Spark 抽欄位 → 使用者確認） | Muse | 待辦 | 優先度低於 T05、T29、T34 |
| T16 | Spark 與 Wonder 的 A/B 比較 | Muse | 待辦 | 10/31 |
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
- [ ] Meta API 金鑰與額度是否可用：未確認。
- [ ] 影片送 Spark 的實際 token 數和費用：未測。
- [ ] SAM 3.1 API 的格式：未讀官方範例（Muse 的 T05）。
- [ ] 用其他工具生成的影片當測試素材是否可以：請 john 在 Discord 確認。
- [ ] 是否允許用其他 AI 寫程式：Discord 原文未取得。

## 待 john 決定

- （無）

## 已做的決定

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

## 成本紀錄（Meta API）

上限：額度 150 美元；後端硬上限 120 美元。每天收工前填。

| 日期 | 項目 | 花費（美元） | 累計 |
| --- | --- | --- | --- |
| | | | 0 |

## 工作日誌（最新在上）

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
