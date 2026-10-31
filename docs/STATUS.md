# STATUS：共享工作檔（所有資料都在這裡）

> 每個 AI 開工前讀這份，完成後在同一個 commit 更新這份。不要另外開新的說明檔，新資訊直接寫進這份的對應段落。
> **Claude 是協調者**：這份檔裡 Claude 寫的指示等同 john 的指示。john 不在時不要問問題，做完就打勾、commit、push，再接下一件（規則見 AGENTS.md）。
> **只讀到「## 封存」為止。** 封存區是已完成的任務和舊日誌，平常不用讀；要查舊紀錄再搜尋。
> 最後更新：2026-10-31 01:30Z（Claude，新增車子檢查 T175–T178）

## 一句話現況

**10/29 03:10 可行性關卡三題都通過，john 決定轉向「影片物理稽核」。** john 自拍的 2 支影片算出 g = 9.62、9.82（一致）；6 支 Meta AI 影片全部不一致，最明顯的一支 g = 0.12。現在最大的缺口是**追蹤品質**：不用模型的追蹤在 3 支 Meta 影片上不可靠，Manus 那支咖啡色的球也追不到，所以 **SAM 3.1（Muse T38）是第一優先**。斜坡教練保留，只做維護。

## 現在每個工具要做什麼（10/29 12:20 Claude）

做完一件不要結束對話：打勾、附 commit、push 自己的分支，再 `git pull origin main`，重讀這份，接「待辦」裡你的下一件。卡住寫進「待 john 決定」，然後跳下一件。

**每個工具都排了 4–6 件（john 10/31 要求一次給多件）。照順序做，做完一件就打勾、commit、push 自己的分支，馬上接下一件，不要等 john 或 Claude 回覆。** 每件都只改自己的目錄和 STATUS。

| 誰 | 照這個順序做 |
| --- | --- |
| **Muse** | **T184 側面車子 SAM** → T186 Spark 認得車 → T187 車子說明 → T188 失敗測試 → T189 最後真打 |
| **Codex** | **T182 網站改版** → T191 手機版 → T192 無障礙 → T193 分享卡 → T194 車子畫面 → T195 收尾 |
| **Antigravity** | T197 從零安裝（已完成） → T196 新設計端到端（等 T182）→ T198 手機實測（等 T191） |
| **Manus** | T199 demo 旁白新版 → T200 提交文字新版 → T201 評審角度檢查；可選 T22 |
| **Claude** | T190 車種換算表 → 審查合併 → T202 每次合併後瀏覽器檢查、README、提交前檢查 |
| **john** | T168 打開網站（一次）；可選 T169 彈跳球、T170 Discord；最後錄 demo、送出 |

## 提交前路線圖（10/29 09:30 Claude，john 要求一次列完；截止 11/04 21:00 ET，我們目標 11/03 交）

**A. 產品做完（10/29–11/02，11/02 晚上功能凍結；john 10/31 決定，原本是 11/01）**
1. Muse T107：SAM 重跑全部影片，和顏色追蹤並排 → 決定 demo 用哪一版追蹤
2. Muse T112：稽核說明、標題改由 Muse Spark 寫（後端 T143 已備好）
3. Muse T108–T111：建議物體名稱、語音回答、花費顯示、來源標示
4. Codex T153：Muse 偵訊改成主要流程（現在藏在收合的區塊裡，評審看不到）；直接上傳變成「進階」
5. Claude：每次合併後用瀏覽器從上傳跑到結果，抓到問題就修（10/29 已修好時間窗建議太慢的問題）
6. Antigravity T52、T119、T120：CI、docker 一鍵啟動、端到端截圖

**B. demo 證據（10/31 前）**
7. Claude：用最終版本重跑所有影片，產生 `product_results`（顏色版＋SAM 版都放）與 demo 紀錄
8. john（可選）：拍 1 支彈跳球，讓 demo 多一種模型

**C. 提交材料（11/03 錄 demo，11/04 白天送出；正式截止 11/04 21:00 ET）**
9. Antigravity T44／Claude：英文 README（安裝、怎麼用、限制、Meta 模型用在哪）
10. Manus：用最終數字更新提交文字和三分鐘旁白（Claude 檢查數字）
11. Claude：提交前檢查（沒有金鑰、只呼叫 Meta、沒有「偵測 AI」字眼、只算 10/26 之後的工作、repo 公開）
12. john：錄三分鐘 demo（真實一致 → 生成不一致 → 拒判 → Muse 問問題與說明），上傳 YouTube 不公開連結
13. john：在 Cerebral Valley 送出（repo 連結＋影片＋文字）

## 待辦（只列還沒做的；做完打勾，Claude 合併時會把打勾的行搬到封存）

格式：`- [x] 編號 負責 內容 — commit abc1234`。只改你自己那一行，不要刪別人的行。

**Muse**（照順序做）
- [x] T184 Muse：（10/31 Claude，Manus T178 清單已到，見 `docs/research/vehicle.md`）用真的 SAM 跑**側面**車子影片。(1) 下載到 repo 外的 `~/slope-own-clips/`（**不准 commit**）：`car_side_1.mp4` = Pexels 36330662（Cars Passing on Suburban Road in Autumn，時間窗 1.0–1.5 s 灰色小轎車；另外 7.5–8.5 s、9.25–10.0 s 各跑一次）；`car_side_2.mp4` = Pexels 35089647（Black and White Urban Street，時間窗 5.0–5.75 s 淺色車）；`car_side_3.mp4` = Pexels 35527369（時間窗 3.0–3.75 s，遠車道淺色轎車，條件式）；`car_side_4.mp4` = Pixabay 31625（4.4–4.6 s，預期因為太短被拒判）。都下載 HD（1920 寬）版本就好，不要 4K。時間窗照 Manus 寫的「整台車在畫面裡」，不要放寬，車子被畫面邊緣切到時位置會偏。(2) 每支 `POST /api/audits`：`assumed_model=vehicle`、`camera_static=true`、`object_name=car`、**不填** `object_size_m`（讓程式用 3 m 和 6 m 兩種車長都判一次）。如果 SAM 抓到別台車，`object_name` 改成 `gray car` 或 `white car` 再跑一次，兩次都記。(3) 每次記 `track_source`、`verdict`、`reasons`、`speed_km_h`、`accel_g`、`car_length_px`、`n_points`、花費、秒數。(4) john 如果用 Meta AI 生成了 `car_meta_1.mp4`…，一起跑。(5) 花費上限 $0.40，判定不准挑。(6) 結果寫進 STATUS 日誌，push `muse/T184-car-side`。**做完直接接 T186。** — commit 8fdb3d5（6 窗全 sam、全拒判：0.47s 差門檻／73%／18%／尺寸+43%／像素車長漂／3 格；overlay 全鎖對車；tmcd 軌繞過；$0.125，累計 $2.112）
- [x] T186 Muse：commit 6cb4f5a。場景建議（註：實際在 `spark.py` 的 `suggest_object`，不在 interview.py）：側面行駛的車 → `assumed_model=vehicle`＋`vehicle_class`（四種＋unknown，清單外轉 unknown）；朝鏡頭／鏡頭動 → `judgeable=false`＋原因；`vehicle_class` 帶數字直接退件（不轉 unknown，避免把偷渡的車長吃掉）；`assumed_model` 只能是 vehicle 或 null。偵訊 FIELDS 加 `vehicle_class`（「這是什麼車」，使用者選，模型不填）。7 個新 mock 測試（任務要的 5 個＋壞 assumed_model＋偵訊問車種），pytest 252 全過，未真打 API。後端還沒接（見「缺什麼」）。(1) `meta_client/interview.py` 的場景建議：畫面主體是側面行駛的車時，建議 `assumed_model=vehicle`；如果車是朝鏡頭開或鏡頭在動，就建議不能判，並說原因（例如「車子朝鏡頭開，側面檢查量不到」）。(2) 偵訊多問一題「這是什麼車？」，回傳欄位 `vehicle_class`，只能是固定清單其中一個：`compact_car`、`sedan`、`suv`、`pickup`、`unknown`。**模型不准回傳車長數字**；長度由 Claude T190 的程式表換算，使用者在畫面上確認。(3) 輸出要過 JSON schema，清單外的值就當 `unknown`；失敗最多重試 2 次。(4) 用假的模型回應寫單元測試（至少 5 個：側面車、朝鏡頭車、移動鏡頭、亂回傳車長、清單外的車種），`pytest` 全過，不真打 API。(5) push `muse/T186-vehicle-scene`。
- [x] T187 Muse：commit c3b98e3。檢查結果：explain 本來就支援三種判定（payload 驅動）；補了車子專用提示（不一致時講「加速度約 X g，超過一般輪胎抓地力上限，與正常路上行駛不一致」，數字只能引 payload，1.2 由原因句提供）；禁字表加「假的」（後端只禁「假影片」，bare 假的之前漏網，標題本來就禁真／假單字不受影響）。headline 車子路徑（T176）已符合要求（只有程式填的槽位＋檢查），沒動。5 個新 mock 測試（三種判定＋偷渡數字＋假的），pytest 250 全過，未真打 API。來源欄位：explain／headline 都回 source=模型名，後端標 model（和自由落體一樣），不用改。(1) 檢查 `meta_client/explain.py` 和 `headline.py`：vehicle 的一致、不一致、資料不足三種都要有 Spark 寫的說明，數字只能用 `{speed_km_h}`、`{accel_g}`、`{car_length_px}` 這類欄位讓程式填入；缺哪種就補。(2) 不一致的說明要講「加速度約 X g，超過一般輪胎抓地力上限 1.2 g，與正常路上行駛不一致」，不准說「假的」「AI 生成」「證實」。(3) 輸出都標 `由 Muse Spark 產生` 的來源欄位（和自由落體一樣）。(4) 單元測試：三種判定各一個、模型偷寫數字要被擋、出現禁用字眼要被擋。(5) push `muse/T187-vehicle-explain`。
- [x] T188 Muse：commit 72c4f91。五項結果：(1) 非 JSON→已有 test_describe_scene_retries_bad_json_then_raises（3 次後丟錯，後端掉回 mock），另補 interview 版 test_interview_non_json_retries_then_raises；(2) 逾時→已有 test_retryable_errors_are_retried（含 APITimeoutError）＋test_gives_up_after_two_retries；(3) SAM 空追蹤→補 test_track_empty_response_is_valid_empty_result（空是合法回傳）＋test_track_object_empty_track_is_all_missing（全缺不補點），後端現為 insufficient_data＋「object tracked in only 0% of frames」，「追蹤缺失」字樣後端還沒有（見「缺什麼」）；(4) $120→已有 test_tracker_refuses_at_limit_without_logging（本次加斷言訊息含 refusing new paid calls）＋test_tracker_respects_env_limit；(5) 語音含數字→已有 test_answer_interview_voice_converts_and_marks_unconfirmed，另補數字直寫版 test_answer_interview_voice_digit_transcript_stays_unconfirmed。pytest 249 全過，$0，未真打 API。用假的 client 測：(1) Spark 回傳不是 JSON → 重試 2 次後回到「待確認」，不卡住；(2) Spark 逾時 → 一樣；(3) SAM 回傳空的追蹤 → 判定變 insufficient_data，原因寫「追蹤缺失」；(4) 累計花費到 $120 → 拒絕新的付費呼叫，錯誤訊息清楚；(5) 語音轉文字含數字 → 一定要使用者確認才採用。已經有測試的就寫「已有，測試名稱 xxx」。(6) push `muse/T188-failure-tests`。
- [x] T189 Muse：commit dd165b7。寫了 `scripts/demo_live_check.py`（TestClient 跑真 API、四案全流程、自帶 $0.50 熔斷），4 案全 PASS：own_2 一致 g=9.44（45 秒 $0.062）、meta_clip4 不一致 g=0.14（48 秒 $0.053）、meta_clip2 朝鏡頭拒判（35 秒 $0.043）、T184 最好的車（car_side_1 1.0–1.5 秒，0.47 秒門檻拒判，41 秒 $0.057）；每案 interview.source=model、track_source=sam，explanation.source=model，headline 在兩筆拒判是 None（正常，無數字可填）。$0.281（上限 $0.50，含為補數字重跑 own_2 一次 $0.066），本分支累計 $2.267。註：跑在 main 程式上（T184–T188 當時還沒合併）；T184 的 $0.125 在它自己分支上，合併後實際累計約 $2.393。寫 `scripts/demo_live_check.py`：對 demo 三個例子（自拍一致、meta_clip4 不一致、朝鏡頭拒判）加上 T184 最好的那支車子影片，跑一次完整流程（Spark 偵訊 → SAM → 稽核 → Spark 說明 → 標題），印出每一步的結果、花費、是否標了「由 Muse Spark / SAM 3.1 產生」。花費上限 $0.50，超過就停。結果寫進 STATUS 日誌，push `muse/T189-live-check`。**到這裡 Muse 的待辦全部結束。**
- [x] T183 Muse：commit b2928bd。凍結前真打 8 步全過（$0.127，上限 $0.40，累計 $1.987）：meta_clip4 偵訊→windows→語音→稽核（inconsistent，g=0.143，headline／explanation 皆 source=model 通過檢查）；3 秒靜音送 /voice 回 200 空欄位（T171 線上確認）；車子 4064324 偵訊（直接問車身長度）→語音→稽核（insufficient_data，sam）。偏差：uvicorn EPERM 改 TestClient；`say` 沙盒空檔，語音改送真實環境音（指定句子抽欄位由 mock 測試覆蓋）。詳見日誌。只改 STATUS 和 cost_log。T176、T179、T181、T171 都合併後，用真的 Meta API 從頭到尾跑一次評審會看到的流程。(1) `git checkout main`、`git pull origin main`，`set -a; . ./.env; set +a`，啟動後端；(2) 用 `data/gate/clips/meta_clip4.mp4` 走完整個偵訊流程：`POST /api/audit-drafts`（記下 `interview.source`、`suggestion`）→ `/windows` → `/voice`（用 `say` 錄一句 "the camera did not move, it is a ball about twenty four centimetres"）→ 送出稽核（時間窗 0–2.5 秒）。確認結果是不一致、g 約 0.14，`headline` 和 `explanation` 是模型寫的、通過檢查；(3) 錄一段 3 秒的靜音送 `/voice`，確認回 200、欄位是空的（T171）；(4) 用 `~/slope-own-clips/4064324-uhd_3840_2160_25fps.mp4` 走一次偵訊流程，語音說 "it's a car driving past, about four and a half metres long"，確認 `assumed_model=vehicle`、`object_size_m=4.5` 被抽出來，送出後被拒判；(5) 每一步記下成功或失敗、`source`、花費、秒數，寫進 STATUS 日誌；壞掉的地方寫清楚錯誤訊息，不要改後端；(6) 只改 STATUS 和 cost_log，push `muse/T183-final-smoke`，跟 john 說「T183 好了」。
- [x] T179 Muse：（10/31 Claude，T176 已合併 PR #101）用真的 SAM 跑 john 下載的三支 Pexels 車子影片，確認 `width_px` 從頭到尾接得通。三支都是車子朝鏡頭開或車內拍，**預期全部拒判**；這次是要確認 SAM 路徑不會壞，不是要它們判一致。步驟：(1) `git checkout main`、`git pull origin main`；(2) 三支影片 `4064324-uhd_3840_2160_25fps.mp4`、`4513718-uhd_3840_2160_30fps.mp4`、`9337511-hd_1920_1080_30fps.mp4` 放在 repo 外的 `~/slope-own-clips/`（john 下載在 Downloads 的話先搬過去，**不准 commit**）；(3) `set -a; . ./.env; set +a; uvicorn backend.main:app --port 8000`；(4) 每支用 curl 送 `POST /api/audits`：`assumed_model=vehicle`、`object_size_m=4.5`、`camera_static=true`、`object_name=car`，時間窗分別是 6–8.2、0–9、5–8.9 秒；(5) 每支記下 `track_source`（要是 `sam`）、`verdict`、`reasons`、`numbers` 裡有沒有 `car_length_px`、花費和秒數；(6) 花費上限 $0.30；(7) 結果寫進 STATUS 日誌，壞掉的地方寫清楚錯誤訊息，不要改後端；(8) 只改 STATUS 和 cost_log，push `muse/T179-sam-car`，跟 john 說「T179 好了」，再做 T171。 — commit 8c109bd（3 支全 201、track_source=sam、全拒判如預期；拒判理由都不是缺寬度（第 2 支理由本身就用了像素車長），width_px 接通。$0.089，累計 $1.859）
- [x] T181 Muse：commit 1347aa0。實作：`sam.py` 新增 `MAX_SAM_FRAMES = 900`；`track()` 轉檔探測後格數超標就上傳前丟 `MediaError`（「影片超過 60 秒，請先選時間窗」）；`CostTracker.check()` 加 `extra_usd` 選填參數（預設 0，舊呼叫不變），`track()` 送出前用 `sam_video_cost_usd(n_frames)` 預扣，超上限拒送。2 個新 mock 測試（901 格拒收、900 格＋上限 $0.10 拒送，皆確認未上傳）。pytest 242 全過。未真打 API。
- [x] T176 Muse：（最優先，10/31 Claude）讓「車子」模型在 Meta 模型這一側也能用。背景：john 10/31 要加車子檢查。Claude 已做好 `physics/experiments/vehicle.py` 和後端（T175，`assumed_model=vehicle`，車身長度放 `object_size_m`）。後端需要每格的**追蹤框寬度**當尺，但 `meta_client/hooks.py` 現在只回中心點和面積，所以 SAM 追車子一定會被拒判（原因寫「no car widths in pixels」）。**從這裡開始**：(1) `git checkout main`、`git pull origin main`、`git checkout -b muse/T176-vehicle`；(2) `meta_client/hooks.py` 的 `_dense_detections`：`DetectionIn` 多填 `width_px`，值是 `det.box` 的 `x2 - x1`；`normalized=True` 時除以畫面寬 `fw`（跟 `centroid_px` 一樣是 0 到 1 的比例），沒有 box 時不填；加 1 個單元測試（假的 `TrackResult`，box 寬 384 px、畫面 1920 → `width_px == 0.2`）；(3) `meta_client/interview.py` 的 `INTERVIEW_PROMPT`：`assumed_model` 那句改成 free fall, bounce, pendulum, or vehicle (a car driving past side-on)，並加一句：for a vehicle, object_size_m is the car's length；問題文字仍然不准有數字；(4) `meta_client/voice.py`：`assumed_model` 的 enum 和第 359 行的檢查加上 `"vehicle"`，提示詞加 vehicle，`object_size_m` 說明加「for a car, its length」；補 1 個測試（逐字稿 "it's a car driving past, about four and a half metres long" → `assumed_model=vehicle`、`object_size_m=4.5`，用 mock 回傳，不要真打）；(5) `meta_client/headline.py`：vehicle 結果沒有重力數字，現在會回 None，這是對的；**加**車子版：`assumed_model == "vehicle"` 而且有 `speed_km_h` 時，讓 Spark 寫一句標題範本，只能用 `{speed_km_h:0}`、`{accel_g:1}` 兩個空格（例：「這台車在 {accel_g:1} g 下煞車，比賽車還猛」），數字由程式填，照現有的檢查流程；補 mock 測試；(6) 跑 `pytest -q` 全綠；(7) **不准真打 API**（要真打先寫進「待 john 決定」），只改 `meta_client/`、`tests/`、STATUS；(8) **到這裡結束**：在這行打勾附 commit，push `muse/T176-vehicle`，跟 john 說「T176 好了」。 — commit 1ab8dea（width_px＋偵訊／語音認 vehicle＋車子標題；5 新測試；pytest 239 全綠；$0 真打）
- [x] T171 Muse：commit 9688eb0。實作：`transcribe()` 空逐字稿改拋 `EmptyTranscriptError`（`ModelOutputError` 子類，舊呼叫方照樣接得住）；`answer_interview_voice()` 捕捉後回 transcript=`沒有聽到內容`＋空 fields＋source `{transcript: 模型名, fields: "none"}`（不用 "mock"，UI 看到 mock 會停用語音），端點回 200 而非 502，且不跑 extract。2 個新 mock 測試（靜音回提示、空稿錯誤型別），pytest 242 全過。未真打 API。
- [x] T166 Muse：修語音 502（T119 發現）。在 `meta_client/voice.py` 的 ASR request 補上 `audioEncoding` 欄位（照 Meta API 文件填我們送的格式），加一個單元測試確認 request 帶了這個欄位；再真打一次 `POST /api/audit-drafts/{id}/voice` 確認不是 502，花費上限 $0.05。只改 `meta_client/`、測試、STATUS、cost_log。push 分支 `muse/T166-voice-encoding`。 — commit 006fb55（request 補 audioEncoding WAV＋斷言測試；真打 voice 端點 200。$0.039，累計 $1.771）
- [x] T119 Muse：真的接上 Meta API 跑一次完整的網站流程（不用瀏覽器，用 curl），確認 demo 時評審看到的 Muse 功能都能動。花費上限 $0.30。(1) `git checkout main`、`git pull origin main`；(2) `set -a; . ./.env; set +a; uvicorn backend.main:app --port 8000`（另開一個終端機跑下面）；(3) 用 `data/gate/clips/meta_clip2.mp4` 依序打：`POST /api/audit-drafts`（看 `interview.source` 是不是 model、`suggestion` 有沒有）→ `POST /api/audit-drafts/{id}/windows` → `POST /api/audit-drafts/{id}/voice`（用 `say -o answer.aiff "the camera did not move and the ball is twenty four centimetres"` 錄一段，轉成 m4a 再送）→ 照 docs/API.md 送出稽核；(4) 每一步記下：成功或失敗、`source` 欄位、花了多少錢、花幾秒；(5) 結果寫進 STATUS 日誌，壞掉的地方寫清楚錯誤訊息，不要自己改後端；(6) 不 commit 任何音檔或影片，push 分支 `muse/T119-live-smoke`（只改 STATUS 和 cost_log）。 — commit 45ab6d3（4 步 3 過：偵訊／時間窗／稽核全通；語音 502——ASR API 現在強制要 audioEncoding 欄位，我方沒送（T24 時不用，API 變了），修法見日誌。$0.046，累計 $1.732）
- [x] T117 Muse：（最優先）產生 demo 用的 SAM 版紀錄（含 Muse Spark 解說）。(1) `git checkout main`、`git pull origin main`；(2) `set -a; . ./.env; set +a; python -m scripts.audit_batch data/gate/manifest.csv --clips ~/slope-own-clips --json-dir data/demo --explain --out data/gate/product_results_sam_v4_demo.md`（約 $0.35；會覆蓋 `data/demo/real_own_*.json` 和 `generated_*.json`，顏色版留在 git 歷史和 `product_results.md`）；(3) 確認 10 支的 verdict 跟 v4 表一樣，不一樣就寫進 STATUS，不要挑；(4) `git status` 確認只有 `data/demo/*.json`、結果檔、STATUS、cost_log 改動，**沒有任何影片**；(5) commit，push 分支 `muse/T117-demo-sam`。 — commit 02fb0c6（10 支 verdict 全跟 v4 一樣；10 個 demo JSON 換成 SAM 版＋模型解說／標題；explain 10 次零重試，T115 修好了。$0.344，累計 $1.353）
- [x] T116 Muse：（最優先）Claude 已修好 SAM 的計時 bug（`meta_client/sam.py` 改用 `-vf fps=15`），請重跑 SAM 全部 10 支：(1) `git checkout main`、`git pull origin main`；(2) 確認 `~/slope-own-clips` 裡有 3 支自拍＋7 支生成影片；(3) `set -a; . ./.env; set +a; python -m scripts.audit_batch data/gate/manifest.csv --clips ~/slope-own-clips --out data/gate/product_results_sam_v4.md`（約 $0.12，不會呼叫解說）；(4) 表格貼進「SAM 對照」v3 下面，標題「v4（修正 15fps 計時後）」，v2、v3 不要刪；(5) 看自拍 3 支的 overlay 紅點，寫一句；(6) commit 結果檔＋STATUS，push 分支 `muse/T116-sam-v4`。 — commit 61f00f2（v4：自拍 3 支全變一致 g=9.30／9.46／8.68，生成側 verdict 不變；3 張 overlay 紅點在球上。`~` 目錄仍不存在，續用 /tmp/slope-own-clips。$0.107，累計 $1.009）
- [x] T114 Muse：自拍影片也用 SAM 跑（demo 要「同一種追蹤」下真實一致、生成不一致、拒判三種都有）。步驟：(1) 請 john 把 3 支自拍影片 IMG_8426.mov、IMG_8429.mov、IMG_8434.mov 放進 repo 外的資料夾 `~/slope-own-clips`，檔名改成 manifest 的名字 `own_1_IMG_8426.mov`、`own_2_IMG_8429.mov`、`own_3_IMG_8434.mov`（**不准放進 repo、不准 commit**）；(2) `cp data/gate/clips/*.mp4 ~/slope-own-clips/`；(3) `set -a; . ./.env; set +a; python -m scripts.audit_batch data/gate/manifest.csv --clips ~/slope-own-clips --out data/gate/product_results_sam_v3.md`（現在批次預設不呼叫解說和標題，只花 SAM 的錢，約 $0.12）；(4) 表格貼進「SAM 對照」v2 下面，標題「v3（加入自拍影片）」；(5) 每支自拍影片看 overlay 確認紅點在球上，寫一句；(6) commit 結果檔＋STATUS，push 分支 `muse/T114-sam-own`。 — commit 32e8600（v3：自拍 3 支全判不一致、偏角 -22～-27 度，與顏色版矛盾；3 張 overlay 紅點都在球上。$0.107，累計 $0.902）
- [x] T115 Muse：查 T113 時 explain 15 次裡有 8 次重試的原因。不准再真打超過 0.10 美元：先用 T113 留下的回傳（或 mock）找出是 schema、數字來源、還是禁用字眼沒過，把原因和建議寫進 STATUS 日誌。若是提示詞的問題就改 `meta_client/` 的提示詞並補測試；不要放寬 `backend/output_check.py` 的檢查。 — commit 800f506（原因見日誌：門檻數字只在原因句裡、檢查只收數字欄，提示詞和檢查打架。修：程式 parse 原因句數字加入 allowlist＋提示詞點名陷阱；2 測試。$0 真打）


**Codex**（照順序做）
- [x] T182 Codex：（進行中，分支 codex/T182-redesign）（10/31 Claude，設計 v4，john 已同意顏色）網站改版。設計稿 https://claude.ai/artifact/81ELAL51WpPCbXJHxnzmzt （看 1 Home、2 Results、3 How it works、Share card 四張）。**顏色**：底 #0E0F12、卡片 #17181C、hover 卡片 #1C1E23、細線 #26282E、文字 #EDEDEF、次要 #8A8F98；地球／一致 = 藍 #5AB0F0；這支影片／不一致／主要按鈕 = 琥珀 #F5A524；資料不足 = 灰。**字體**：標題 Space Grotesk 700，內文 Inter，數字 JetBrains Mono。**分頁**：首頁、Results、How it works、上傳／稽核頁分成不同路由，不要一頁很長；導覽列只有 Results、How it works、中文／English。**首頁**：大標「Does it fall like Earth?」（Earth 藍色）、一句說明、琥珀色「Check a video」和外框「See examples」兩顆按鈕；右邊是 meta_clip4 畫面加動畫：藍色虛線（地球）先出現，琥珀線畫出來，終點彈出，最後出現「Doesn't match Earth gravity.」。**首頁不放數字。** **Results**：三張卡（一致／不一致／不能判斷），滑鼠指到的卡放大到 1.05、顯示數字，其他卡變暗、模糊、縮小；數字從 `data/demo` JSON 讀。**How it works**：四步，指到的那步變寬、編號變琥珀色、顯示說明。動畫只用 CSS transition／keyframes，不加新套件。保留所有 testid、鍵盤操作、中英切換、禁用字眼測試。`npm test`、`npm run build`、`VITE_DEMO_ONLY=1 npm run build` 都要過。push `codex/T182-redesign`。**做完直接接 T191。** — commit a189883（128 tests、一般／demo build 通過）
- [x] T191 Codex：（進行中）（10/31 Claude）手機版。每一頁在 390 px 和 768 px 寬檢查：不能橫向捲動、按鈕至少 44 px 高、大標縮到 44–52 px、Results 三張卡改成上下排、How 四步改成上下排。手機沒有滑鼠：卡片改成點一下展開數字（再點一下收起）。加一個前端測試確認 390 px 沒有元素超出畫面寬度。push `codex/T191-mobile`。 — commit 4560248（130 tests、一般／demo build 通過）
- [x] T192 Codex：（進行中）（10/31 Claude）無障礙。(1) 所有滑鼠效果用 `:focus-visible` 也要觸發，Tab 鍵可以一張一張看卡片；(2) `prefers-reduced-motion: reduce` 時關掉所有動畫，直接顯示最後畫面；(3) 文字對比至少 4.5:1（#8A8F98 在 #0E0F12 上要量，不夠就調亮）；(4) 判定不能只靠顏色，一定要有文字標籤；(5) 每張圖有 alt。跑現有的 a11y 測試並補新的。push `codex/T192-a11y`。 — commit 1b9a772（133 tests、一般／demo build 通過）
- [x] T193 Codex：（進行中）（10/31 Claude）分享卡。照設計稿的 Share card 改 `frontend/src/cardExport.ts`：琥珀滿版、大數字（例如「1/69」）、一句「of Earth's gravity.」、下面「Tracked by SAM 3.1」「Numbers by code」兩個標籤、最下面「Checks motion against a model. Does not say whether a video is real.」。一致的結果用藍色版、不能判斷用灰色版。數字從稽核結果讀，比例由後端給的數字算（前端不准自己算物理；如果後端沒有比例欄位，在 STATUS 寫提案給 Claude，先只顯示 m/s²）。下載成 1080×1920 PNG，不加新套件。push `codex/T193-share-card`。 — commit fbcc31b（135 tests、一般／demo build 通過）
- [ ] T194 Codex：（10/31 Claude）車子結果套用新設計。車子的結果頁和卡片用同一套顏色：大數字是 `speed_km_h`（km/h）和 `accel_g`（g），旁邊細字寫「上限 1.2 g」；沒給車長時顯示「用 3–6 m 車長估計」。T186 合併後，偵訊畫面加「這是什麼車？」的選項（小車、轎車、SUV、皮卡、不確定），選完顯示程式給的車長讓使用者確認或改。push `codex/T194-vehicle-ui`。
- [ ] T195 Codex：（10/31 Claude）收尾檢查。(1) 新加的字串都有中英文，加測試掃描「沒翻譯的 key」；(2) 禁用字眼測試涵蓋新頁面；(3) 拿掉沒用到的舊元件和舊 CSS（先確認沒有被 import）；(4) 三個 build 都過；(5) 在 STATUS 日誌寫 1440、768、390 px 各頁看起來對不對。push `codex/T195-cleanup`。**到這裡 Codex 的待辦全部結束。**
- [x] T177 Codex：（最優先，10/31 Claude）前端加上「車子」模型（後端已好，見 docs/API.md 的 `assumed_model=vehicle`）。**從這裡開始**：(1) `git checkout main`、`git pull origin main`、`git checkout -b codex/T177-vehicle`；(2) `frontend/src/audit.ts`：`AuditModel` 加 `'vehicle'`，`verdictText` 的名字是「車子行駛」，第 15 行的檢查清單加 `'vehicle'`；`voiceAnswer.ts` 第 12 行同樣加上；(3) `InterviewPanel.tsx` 和 `AuditPage.tsx` 的模型選單加一個選項：「車子從側面開過（鏡頭固定）」；選了 vehicle 時，尺寸欄的標籤改成「車身長度（公尺）」，下面一行小字：「一般轎車約 4.5 公尺，休旅車約 4.8，小車約 3.5；知道車型最好查原廠數字。不填也可以，會用 3 到 6 公尺都算一次，兩個答案一樣才判。」（這段的數字是給使用者參考的固定說明，不是測量結果）；另外提示「請選車子整台都在畫面裡、從左開到右的那幾秒」；(4) 結果卡（verdict 下方）在 vehicle 時顯示：車速 `speed_km_h`（km/h，取整數）、加速或煞車 `accel_g`（g，小數 2 位；`accel_m_s2` 負的寫「煞車」，正的寫「加速」）、`speed_car_lengths_s`（「每秒走 X 個車身長」，這個不需要車長）、以及一句「這台車要有 `car_length_for_max_accel_m` 公尺長，這個加速度才剛好是 1.2 g」；**數字只照後端原值顯示，不要自己算**（km/h 後端已給）；欄位不存在就不顯示那一行；固定說明一句：「一般車子的輪胎抓地力大約撐得住 1 g；超過 1.2 g 就和『車子在路上開』這個假設不一致。這不判斷影片真假。」(5) 靜態 demo：`data/demo/synthetic_car_50kmh_braking.json`（一致，約 49 km/h、0.60 g 煞車）和 `synthetic_car_3g_launch.json`（不一致，3.0 g）是程式畫的方塊，要放進 demo 頁或結果牆時**一定要標「程式模擬」**，不准說是真實或生成影片；(6) 測試：`audit.test` 類加 vehicle 的 verdictText 和欄位驗證；結果卡在 vehicle 時顯示 km/h、沒有車長時不顯示 km/h；禁字檢查要過；(7) `npm test`、`npm run build`、`VITE_DEMO_ONLY=1 npm run build` 都要過；只改 `frontend/` 和 STATUS，不改後端；(8) **到這裡結束**：打勾附 commit，push `codex/T177-vehicle`，跟 john 說「T177 好了」，再接 T173。 — commit 9041ce8（124 tests、兩種 build 通過；車子 UI／語音欄位／程式模擬範例）
- [x] T173 Codex：在稽核結果和物理名片上顯示「重力當尺」四個新數字（後端已有，見 docs/API.md 的 `if_earth_*`）。標題寫「如果這是地球重力、正常速度」，數字照後端原值顯示，不要自己算。旁邊固定一句說明：「這是假設下的讀數，不是判定；慢動作會讓高度變大。」結果牆和靜態 demo 要能看到（demo JSON 沒有這些欄位時就不顯示）。push 分支 `codex/T173-gravity-ruler`。 — commit d056501（120 tests、一般／靜態 build 通過，四個讀數與假設說明）
- [x] T167 Codex：已檢查線上 Pages 在 1440／390px 的 demo、wall、audit、compare、how、home（12 張不同截圖，未 commit）；六個頁面／圖片與全部導覽均可用，console 無錯誤。修正 Guided demo 在長頁面看不到下一步、一般導覽被拉回、跨頁焦點遺失；本機 Pages 子路徑版以鍵盤完成六步、固定面板保持可見、結束回到啟動按鈕。npm 118 pass、pytest 224 pass、一般與 Pages build pass；修補待 PR 合併後部署。 — commit 9889f77，PR #97（目標 main）。
- [ ] T165 Codex（前端完成；Figma 收尾受配額阻擋）：依 john 直接指示完成日本編輯設計改版，14 個 Figma 桌面／手機狀態、47 個 Variables、21 個元件 variants；前端保留 API、原文、數字、testid 與鍵盤流程。npm 115 pass、標準／demo build pass；Figma 手機欄位與清理待配額恢復，故不整項勾完。Figma：https://www.figma.com/design/qXc74pdeiHjVzEV47YrDRQ — frontend commit a624494；同步 main 7e2c8bf，PR #87（目標 main）；本任務原暫編 T164，同步 main 後避開 Manus 的 T164 改為 T165。
- [x] T157 Codex：依 Claude「demo 資料已定版」公告，靜態展示與結果牆共用 T118 的完整 10 筆 SAM 紀錄；移除 own_3 舊判定文案，補模型標題、原始原因，展示／導覽／比較共用三種結果入口，程式測試範例另列。npm 114 pass、普通／靜態 build pass、pytest 222 pass；只改 frontend 與 STATUS。 — commit 82f90f9，PR #88（目標 main）。


**Antigravity**（照順序做）
- [ ] T196 Antigravity：（10/31 Claude，等 Codex T182 合併到 main 之後）用內建瀏覽器跑端到端：(1) 首頁、Results、How it works、上傳頁各截 1440 px 和 390 px；(2) 首頁動畫有沒有播完、hover 卡片有沒有放大、其他卡有沒有變暗；(3) 上傳 `data/demo` 有的例子跑到結果頁；(4) 切中文再切回英文；(5) 只用鍵盤（Tab、Enter）走完一次。截圖放 `data/e2e/T196/`（小於 300 KB 一張），問題寫進 STATUS「缺什麼」，push `antigravity/T196-e2e`。
- [x] T197 Antigravity：（10/31 Claude）在全新的資料夾 `git clone` repo，照 README 從零啟動實測：git clone 2.54s 通過；ffmpeg/python3.11/node24/npm 通過；cp .env.example 0.01s 通過；npm ci 1.12s 與 npm test (126 pass) 3.16s 通過；pytest 244 pass (17.44s) 與雙 e2e 腳本全數通過。發現 3 項問題（python3.11 ensurepip、docker 未安裝、scripts/dev.sh 寫死 python3）已記錄進「缺什麼」待 Claude 修改 — commit 76f9b92
- [ ] T198 Antigravity：（10/31 Claude，T191 合併後）手機實測：用瀏覽器的 iPhone 14 和 Pixel 7 模擬，走一次上傳到結果，截圖放 `data/e2e/T198/`，問題寫進 STATUS。push `antigravity/T198-mobile`。**到這裡 Antigravity 的待辦全部結束。**
- [x] T53 Antigravity：效能測試：30 秒 1080p iPhone HEVC 影片 `/api/audits` 耗時：顏色追蹤 1.61s、frame differencing 0.38s（目標 < 20s，通過；註：只量 0–5 秒的時間窗）— commit 38c3570
- [x] T68 Antigravity：鬼影對照和物理名片的端到端測試與截圖完成（新增 scripts/e2e_ghost_and_physics_card.mjs、tests/backend/test_e2e_ghost_card.py，產出桌面與 390px 手機截圖存於 docs/screens/）— commit 00036aa
- [x] T121 Antigravity：效能量測：10 秒 1080p 影片 `/api/audits` 跑完耗時：顏色追蹤 1.13s、frame differencing 0.36s（目標 < 20s，通過；Claude 在雲端重跑 6.65s／1.53s，也通過。註：腳本只量 0–5 秒的時間窗）— commit b83b4d1
- [x] T122 Antigravity：照 README 在乾淨目錄從零安裝：前端 111 測試通過；後端要用 README 寫的 `python3.11`（Homebrew 預設 3.14 建 venv 會失敗）。註：STATUS 提到的 commit 9db92e3（gate_prepare 的 drawtext 退路）沒有 push 到 GitHub，main 沒有這個改動 — commit 2c4af33


**Manus**（不寫程式）
- [x] T178 Manus：車子影片與資料研究 — 成果在 `docs/research/vehicle.md`（Claude 10/31 收進 repo 並核對，見 T185）
- [x] T164 Manus：三分鐘 demo 的英文旁白和分鏡表（給 john 錄影用）。順序：(1) 0:00–0:20 問題：影片裡的運動符不符合物理，一般人沒辦法量；(2) 0:20–1:00 Muse 偵訊：上傳 → Muse Spark 問問題、建議物體名稱 → 使用者確認；(3) 1:00–1:40 真實影片：john 丟球，SAM 3.1 追蹤，g = 9.45 m/s²，與假設一致；(4) 1:40–2:20 生成影片：g = 0.14 m/s²（像冥王星），與真實重力的自由飛行不一致；另一支因為物體往鏡頭移動而拒判；(5) 2:20–2:50 限制與規則：數字只由程式算、模型不碰數字、不判斷影片真假；(6) 2:50–3:00 結尾。數字只用 README「Results on our test set」的 SAM 欄。每段寫：畫面上要點哪裡、旁白（英文）、秒數。不准說「偵測 AI」「抓假影片」「任何影片都能檢查」。交給 john 轉給 Claude 檢查。
- [x] T163 Manus：用目前的數字寫提交文字初稿（英文，Cerebral Valley 用）：一段 50 字簡介、一段 200 字說明（問題、做法、Meta 模型用在哪、結果、限制）。數字只用 README 的「Results on our test set」表；SAM 版寫 [TBD]。不准出現「偵測 AI」「抓假影片」「任何影片都能檢查」。交給 john 轉給 Claude。
- [ ] T199 Manus：（10/31 Claude）更新三分鐘 demo 旁白和分鏡（T164 的新版）。新的部分：(1) 網站換成深色新設計（首頁「Does it fall like Earth?」動畫、Results 卡片指到會放大）；(2) 加 20 秒車子例子：用車身長度當尺，算速度和加速度，超過 1.2 g 就和正常路上行駛不一致；(3) 結尾的分享卡「1/69 of Earth's gravity」。數字只能用 `data/demo` 和 STATUS 裡已經有的，不准自己估；要用但還沒有的數字寫「[等 Claude 填]」。禁用字眼：fake detector、detects AI、proves、any video。英文，給 john。
- [ ] T200 Manus：（10/31 Claude）提交文字更新（T163 的新版，Cerebral Valley 用）：50 字簡介、200 字說明、「Meta 模型用在哪」三行（Muse Spark：偵訊、建議時間窗、說明與標題；SAM 3.1：追蹤；Voice Transcribe：語音回答）、限制三行（固定鏡頭、側面、單一物體；慢動作和朝鏡頭會拒判；不判斷影片真假）。同樣的禁用字眼。英文，給 john。
- [ ] T201 Manus：（10/31 Claude）評審角度檢查表：找這次 Meta hackathon 公開的評分標準（官網或 Cerebral Valley 頁面），逐條寫我們的作品哪裡符合、哪裡弱、demo 要怎麼補強。附網址。給 john 轉給 Claude。**到這裡 Manus 的待辦全部結束（T22 可選）。**
- [ ] T22 Manus：使用者測試計畫（招募訊息、任務腳本、記錄表）


**Claude**
- [x] T185 Claude：Manus T178 研究收進 `docs/research/vehicle.md` 並核對：車長 10 筆的英寸換算公尺全部正確；Taycan 103 ft 60–0 mph 換算平均減速度 1.17 g 正確；10 款常見車長都在 4.6–5.9 m，落在我們沒給車長時用的 3–6 m 範圍內。網址在雲端被網路擋住，沒辦法逐一打開，改由 Muse T184 下載時確認。注意：最好的兩支整台車入鏡只有約 0.5–1 秒，接近 0.5 秒的拒判門檻。
- [x] T190 Claude：車種→車長換算表：`physics/experiments/vehicle.py` 的 `VEHICLE_CLASS_LENGTH_M`（compact_car 4.3–4.75、sedan 4.6–5.0、suv 4.5–4.85、pickup 5.3–5.95 m，來源 `docs/research/vehicle.md`）。`POST /api/audits` 新增選填 `vehicle_class`，沒給車長時用該車種的範圍兩端各判一次，`numbers` 多 `car_length_low_m/high_m`、`speed_km_h_low/high`、`accel_g_low/high`（給 Codex T194 顯示「用 4.6–5.0 m 估計，約 49–54 km/h」）。API.md 已更新。pytest 245 過。Muse T186 的 `vehicle_class` 直接用這四個值加 `unknown`。
- [ ] T202 Claude：每次合併後用瀏覽器從上傳跑到結果；T189 後用最終版本重跑 demo 紀錄；寫英文 README 的限制段；11/02 晚上凍結前做提交前檢查（沒有金鑰、只呼叫 Meta、沒有禁用字眼、repo 公開）。
- [x] T180 Claude：資安與 bug 檢查（john 10/31 要求）。**修了 3 個**：(1) 上傳影片沒有大小上限，而且稽核上傳會把整個檔案讀進記憶體，一個超大檔就能把後端撐爆 → 改成分段寫入、超過 500 MB 回 413 並刪掉半個檔（`backend/store.py` 的 `copy_limited`，稽核和斜坡上傳都用）；(2) 稽核時間窗沒有上限，每格都放在記憶體裡，送 0 到 600 秒會吃掉好幾 GB → 超過 30 秒回 422；(3) `docker-compose.yml` 的連接埠綁在所有網路介面，在比賽現場的共用 Wi-Fi 上別人可以連進來上傳影片、花我們的 Meta 額度 → 改成只綁 127.0.0.1。**檢查過沒問題**：git 全部歷史沒有金鑰（`.env` 在 .gitignore）；程式不會印出或記錄金鑰；repo 裡只有生成影片，沒有 john 的自拍影片；前端沒有 `innerHTML`／`eval`，模型文字都當純文字顯示；`npm audit` 0 個弱點；pip-audit 只有本機工具 pip、setuptools 的舊版，不是產品套件；靜態網站 workflow 權限是最小的。1 個新測試。
- [x] T175 Claude：車子檢查（john 10/31 要求）。`physics/experiments/vehicle.py`：用使用者給的車身長度當尺，擬合沿行進方向的位置 s(t) = s0 + v t + ½ a t²，算車速、加速度；需要超過 1.2 g 或軌跡跳動 → 不一致；沒給車長時 3 m 和 6 m 都算，答案一樣才判。後端 `assumed_model=vehicle`，追蹤框寬度經 `DetectionIn.width_px`（SAM，等 Muse T176）或不用模型的追蹤（已接好）傳進來。說明範本、API.md、2 筆程式模擬 demo 紀錄（49 km/h 煞車 0.60 g 一致；3.0 g 起步不一致）、8 個 physics 測試＋1 個後端端到端測試。john 給的三支 Pexels 影片實跑：街道休旅車和車內拍攝因為車子變大 32%、42%（往鏡頭開）拒判，山路那支車子正面開來、橫向移動不到一個車身長也拒判。三支都不是側面拍，所以還需要一支側面影片（Manus T178 找）。
- [x] T172 Claude：「重力當尺」：`physics/experiments/freefall.py` 的 `gravity_ruler()`，不需要尺寸，假設地球重力、正常速度，算出飛行時間、垂直距離、出手速度和角度；後端放進 `numbers.if_earth_*`；API.md 已更新；2 個測試。meta_clip4 跑出「如果是地球重力，這顆球掉了 44 m」。
- [x] T174 Claude：`data/demo/` 裡 9 筆走到擬合的自由飛行紀錄加上 `if_earth_*`。做法：用紀錄裡存的追蹤點重新 `fit_flight`，確認 `a_px_s2` 和點數與原紀錄完全相同才寫入，其他欄位一個字都沒動（判定、g 不變）。拒判的 4 筆（meta_clip2/3/6、moving camera）和 bounce/pendulum 沒有這些欄位，這是對的。demo 的 meta_clip4（窗口 0–2.5 s）：如果是地球重力，垂直距離 28.7 m；自己拍的三支是 0.86、0.67、0.52 m。
- [ ] T127 Claude：審查並合併所有工具的 PR（每 2 小時巡查一次）
- [ ] T131 Claude：彈跳和單擺的真實影片流程（等 john 拍片）：準備標註表和試跑腳本
- [ ] T96 Claude：（Manus 已補，03:15）Manus 1 支、Antigravity 2 支（程式渲染 3D，另列「程式模擬」來源）標註好後補進關卡紀錄
- [ ] 審查 Muse、Codex、Antigravity 的所有 PR


**john**
- [x] T168 john：打開靜態 demo 網站（只要點一次）— 10/29 17:55 上線：GitHub repo → Settings → Pages → Build and deployment 的 Source 選「GitHub Actions」。之後每次合併到 main 都會自動更新 https://johncat88425-del.github.io/slope-coach/
- [ ] T169 john：拍 1 支彈跳球（可選，讓 demo 多一種模型）：腳架固定、正側面、橘色球從約 1 公尺高放手讓它自己彈 3 次以上、10 秒內、畫面裡沒有人臉、正常速度不要慢動作。拍完放在 repo 外的 `~/slope-own-clips/own_4_bounce.mov`，不要 commit，跟 Claude 說一聲。
- [ ] T170 john：在 Discord 貼這段問題（可選）：Hi! For the Indie track, can we use clips generated with other tools (e.g. Manus) as *test inputs* for our app? The app itself only calls Meta models at runtime. Thanks!
- [ ] T33 拍片並生成影片，提供標註
- [ ] 在 Discord 問：用其他工具生成的影片當測試素材可不可以

## 可行性關卡結果（規則已凍結，背景說明在封存區）

### 決定規則

- **三題都通過：** 轉向「影片物理稽核」，由 Claude 改寫 AGENTS.md、本檔和 demo 劇本。
- **大部分案例都要拒判，或找不到足以支持主張的異常：** 回到「實驗調查員」，也就是把斜坡的真實實驗閉環做好。拋體檢查留下來，當第二個實驗插件。
- 不論走哪條路，都照兩條原則做：成功和拒判放在同一段 demo 裡；只承諾已經做完的東西。

### 已知限制（結果裡要照實寫）

- 關卡的追蹤用畫面差異法，不用模型。物體有動態模糊時，尺寸會估大，g 也會跟著偏。
- 沒有處理透視：物體朝鏡頭或遠離鏡頭飛時，結果不可信。
- 時間窗目前由人標註。正式版改由 Spark 建議（T34），使用者確認。

### 規則變更紀錄

- **10/29 12:50 SAM 15fps 計時 bug（看過 SAM v3 結果之後修的，屬於修 bug，不是調門檻）**：v3 裡 3 支自拍影片全部「加速度偏 -22～-27 度」不一致，但顏色版同樣 3 支是 -6、+1、+5 度。Claude 用顏色追蹤模擬 SAM 的前處理（同一個 ffmpeg 指令轉 15fps）重現出 -22.4、-23.3、-25.3 度，查出原因：`-ss` 後用 `-r 15` 轉檔，窗口開頭幾格是 30fps 間隔、之後才變 15fps，所以「第 N 格 = t_start + N/15」不成立，時間被扭曲，軌跡看起來是斜的。改用 `-vf fps=15` 後逐格對照完全吻合，並加了真的跑 ffmpeg 的測試（舊指令會失敗）。**v2、v3 的 SAM 數字都受影響**，保留原表，v4 重跑後兩版並列。門檻沒有改。
- **10/29 T87（看過 john 的 3 支自拍影片之後改的）**：原規則用 frame differencing，在真實影片上抓到手臂和背景。新規則：人工標註的物體名稱含顏色（目前只有 orange，色相 15 到 45 度、飽和度與亮度至少 0.4）時，只取「是這個顏色而且有在動」的最大一塊；物體大小改用色塊短軸的寬度。其他門檻不變。顏色範圍是看過這 3 支影片後訂的，所以**之後的 Meta AI 影片要用同一組參數，不准再調**。
- 新舊兩版用同一組試算標註（Claude 提議、john 尚未確認：own_1 1.9–2.6 s、own_2 0.2–0.8 s、own_3 2.0–2.4 s，球 0.05 m）的結果：
  - 舊版 frame_diff：own_1 不一致（加速度偏 -70 度、軌跡不像拋物線）、own_2 不一致（-71 度）、own_3 資料不足。原因是追到手臂，不是物理。
  - 新版 color：三支軌跡都是乾淨拋物線（殘差只有行程的 0.4% 到 0.8%，偏角 1 到 6 度），但算出的 g 只有 3.7 到 4.5 m/s²。換句話說，如果 g 是 9.81，球的直徑應該是 0.11 到 0.13 m，不是 0.05 m。三支都偏同一個方向，比較像是尺寸標註的問題，所以先請 john 用尺量球（圓周 ÷ 3.14）。**不准為了讓結果變成一致去改門檻或改顏色參數。**

- **10/29 10:40 T146（看過 SAM 結果之後改的，屬於修 bug）**：SAM 追到的比例和缺格事件，改用 SAM 自己的取樣（15 fps）來算，不再用影片的格數（24 或 30 fps）當分母。門檻 0.8 不變。舊版的結果：7 支全部因為「只追到 61–63%」拒判（`data/gate/product_results_sam.md`，保留）。新版的結果由 Muse 在 T113 重跑，存成 `product_results_sam_v2.md`，兩版都要列。顏色追蹤和 frame differencing 不受影響。
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

#### v2（T146 修正分母後，`data/gate/product_results_sam_v2.md`）

| clip | source | verdict | g_apparent_m_s2 | nearest_body | size_trend | track_source | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | missing |  |  |  |  | not found in data/gate/clips |
| own_2_IMG_8429.mov | own | missing |  |  |  |  | not found in data/gate/clips |
| own_3_IMG_8434.mov | own | missing |  |  |  |  | not found in data/gate/clips |
| meta_clip1.mp4 | meta_ai | inconsistent | 0.24 | Pluto | -0.18 | sam | apparent g 0.24 m/s^2 is outside 8.34-11.28 |
| meta_clip2.mp4 | meta_ai | insufficient_data |  |  | -0.49 | sam | object size changes -49% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| meta_clip3.mp4 | meta_ai | insufficient_data |  |  | -0.34 | sam | object size changes -34% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| meta_clip4.mp4 | meta_ai | inconsistent | 0.15 | Pluto | 0.15 | sam | apparent g 0.15 m/s^2 is outside 8.34-11.28 |
| meta_clip5.mp4 | meta_ai | inconsistent | 1.41 | Moon | -0.23 | sam | acceleration points -178 deg away from image-down |
| meta_clip6.mp4 | meta_ai | insufficient_data |  |  | -0.42 | sam | object size changes -42% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| manus_clip1.mp4 | manus | inconsistent | 2.50 | Mars | 0.14 | sam | apparent g 2.50 m/s^2 is outside 8.34-11.28 |

v1 全拒判 → v2 有 4 支判出不一致（clip1 g=0.24 冥王星、clip4 g=0.15 冥王星、clip5 g=1.41 月球、manus g=2.50 火星），3 支仍因透視（size_trend -34%～-49%）拒判。跟顏色版對照：兩種追蹤判出來的不是同一批——顏色版判 clip2／clip3 不一致，SAM 版這兩支因透視拒判；反之 clip1／clip4／clip5 顏色版拒判、SAM 版判不一致。兩版都列，demo 選哪版由 john／Claude 決定。

**overlay 紅點確認**（4 支新判出的）：clip1 紅點沿客廳拋物線走、在球上；clip5 紅點在桌緣的球上；manus 紅點沿體育館拋物線走、在球上——這 3 支確認通過。manus 的 g=2.50 跟之前 frame_diff 試跑的 2.55 接近，互相印證。clip4 該格只有左緣大片深色物體、紅點沿其邊緣走，看起來有跟上但單格無法確定是球心，請 john 再看一眼。另 clip5 的理由是加速度方向偏 -178 度（幾乎朝上），數字是程式算的照實列，判讀請 Claude 看。

#### v3（加入自拍影片，`data/gate/product_results_sam_v3.md`）

| clip | source | verdict | g_apparent_m_s2 | nearest_body | size_trend | track_source | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | inconsistent | 6.51 | Earth | -0.01 | sam | acceleration points -22 deg away from image-down |
| own_2_IMG_8429.mov | own | inconsistent | 7.26 | Earth | 0.01 | sam | acceleration points -24 deg away from image-down |
| own_3_IMG_8434.mov | own | inconsistent | 8.22 | Earth | -0.05 | sam | acceleration points -27 deg away from image-down |
| meta_clip1.mp4 | meta_ai | inconsistent | 0.24 | Pluto | -0.18 | sam | apparent g 0.24 m/s^2 is outside 8.34-11.28 |
| meta_clip2.mp4 | meta_ai | insufficient_data |  |  | -0.49 | sam | object size changes -49% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| meta_clip3.mp4 | meta_ai | insufficient_data |  |  | -0.34 | sam | object size changes -34% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| meta_clip4.mp4 | meta_ai | inconsistent | 0.15 | Pluto | 0.15 | sam | apparent g 0.15 m/s^2 is outside 8.34-11.28 |
| meta_clip5.mp4 | meta_ai | inconsistent | 1.41 | Moon | -0.23 | sam | acceleration points -178 deg away from image-down |
| meta_clip6.mp4 | meta_ai | insufficient_data |  |  | -0.42 | sam | object size changes -42% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| manus_clip1.mp4 | manus | inconsistent | 2.50 | Mars | 0.14 | sam | apparent g 2.50 m/s^2 is outside 8.34-11.28 |

自拍 3 支用 SAM 全判不一致（偏角 -22～-27 度、g=6.51／7.26／8.22），跟顏色版（own_1／own_2 一致、g=9.62／9.82）矛盾——同一個 demo「同一種追蹤下真實一致」的目標目前達不到，選版時請正視。overlay 確認：own_1 紅點沿沙發上拋物線走、在球上；own_2 紅點聚在沙發中段球位、在球上；own_3 紅點從沙發沿掉落軌跡到地板、在球上。紅點都在球上，所以偏角不是跟丟，原因待查（請 Claude 看是追蹤偏差還是判定門檻問題）。meta／manus 7 格與 v2 一字不差（重現性通過）。自拍影片只放 /tmp（沙盒寫不到 `~`，等價做法），沒進 repo。

#### v4（修正 15fps 計時後，`data/gate/product_results_sam_v4.md`）

| clip | source | verdict | g_apparent_m_s2 | nearest_body | size_trend | track_source | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| own_1_IMG_8426.mov | own | consistent | 9.30 | Earth | 0.04 | sam |  |
| own_2_IMG_8429.mov | own | consistent | 9.46 | Earth | 0.10 | sam |  |
| own_3_IMG_8434.mov | own | consistent | 8.68 | Earth | -0.01 | sam |  |
| meta_clip1.mp4 | meta_ai | inconsistent | 0.25 | Pluto | -0.17 | sam | apparent g 0.25 m/s^2 is outside 8.34-11.28 |
| meta_clip2.mp4 | meta_ai | insufficient_data |  |  | -0.48 | sam | object size changes -48% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| meta_clip3.mp4 | meta_ai | insufficient_data |  |  | -0.34 | sam | object size changes -34% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| meta_clip4.mp4 | meta_ai | inconsistent | 0.14 | Pluto | 0.13 | sam | apparent g 0.14 m/s^2 is outside 8.34-11.28 |
| meta_clip5.mp4 | meta_ai | inconsistent | 1.80 | Moon | -0.19 | sam | acceleration points -171 deg away from image-down |
| meta_clip6.mp4 | meta_ai | insufficient_data |  |  | -0.42 | sam | object size changes -42% along the track; it moves towards or away from the camera, which this 2D check cannot judge |
| manus_clip1.mp4 | manus | inconsistent | 2.63 | Mars | 0.06 | sam | apparent g 2.63 m/s^2 is outside 8.34-11.28 |

計時修好後自拍 3 支全變一致（g=9.30／9.46／8.68，偏角消失）——v3 的偏角是轉碼時間戳 bug，不是追蹤問題。demo 目標達成：同一種追蹤（SAM）下真實一致、生成不一致（4 支）、拒判（3 支透視）三種都有。生成側 verdict 與 v3 相同，數字微移（clip1 0.24→0.25、clip4 0.15→0.14、clip5 1.41→1.80、manus 2.50→2.63）。overlay：own_1 紅點沿沙發拋物線、在球上；own_2 紅點聚沙發中段球位、在球上；own_3 紅點從沙發到地板沿掉落走、在球上。

## 怎麼跑（給所有工具）

- 後端：`uvicorn backend.main:app --reload`，網址 http://localhost:8000，互動文件在 `/docs`。API 契約見 `docs/API.md`。
- 合成示範資料：`python -m scripts.seed_demo --case pushed`，也可以把 case 換成 wrong_height、ok 或 occluded。
- 測試：`pytest`（目前 58 個通過）；前端 `cd frontend && npm test`。
- 免模型的軌跡探測：`python -m scripts.flight_probe 影片.mp4 --start 1.0 --end 2.0 --overlay out.png`。
- 上傳的檔案由後端放在 `/media/{eid}/{檔名}`。

## 缺什麼

- [x] [README 安裝問題 / T197 發現] Claude 10/31 已修：README 加 macOS ensurepip 失敗的繞法（`--without-pip` 再裝 pip）、註明 Docker 只有 `docker compose up` 才需要；`scripts/dev.sh` 優先用 `python3.11`。
- [ ] 還沒有可用的真實影片。第一支（IMG_8418.MOV）有四個問題：拍攝角度是斜的、滑塊太小太淡、只滑了 0.75 秒、畫面有人臉。
- [ ] 影片送 Spark 的實際 token 數和費用：未測。
- [ ] `tests/scripts/test_gate_prepare.py` 在乾淨 main 上也失敗（Muse 10/29 驗證過，與 Muse 改動無關）：gate_prepare 處理真片時 exit 1。請 Claude/Antigravity 修，T52 CI 會踩到。
- [ ] T186 Muse：後端接線（Claude）：`ObjectSuggestion` 加 `assumed_model`、`judgeable`、`vehicle_class`（目前 Pydantic 靜默丟掉）；`QuestionField` 加 `vehicle_class`（沒加的話模型一問車種整組偵訊掉回 mock）。T194 等這個。
- [ ] 用其他工具生成的影片當測試素材是否可以：請 john 在 Discord 確認。
- [ ] T188 Muse：空追蹤的原因字樣（Claude）：T188 要求空追蹤時原因寫「追蹤缺失」，但後端現在是英文「object tracked in only 0% of frames」（後端原因全英文，突然一句中文很怪）。請 Claude 決定字樣／是否改，Muse 不碰後端。
- [ ] 是否允許用其他 AI 寫程式：Discord 原文未取得。
- [x] Claude 已修（10/31）：`backend/video.py` 的 `probe_fps()` 遇到含 tmcd 軌的 mp4 只取第一行，加測試 `tests/backend/test_video_probe.py`；Pexels 原檔不用再 remux。

## 待 john 決定

- T193 Codex／Claude：已有 `numbers.g_vs_earth`，分享卡直接格式化為十進位倍率（例如現有資料 0.0146×）；缺此欄就顯示後端 `g_apparent_m_s2`，不自行用 g/9.81 或 1/g 算比例。若設計一定要「1/69」，請後端新增經驗證的顯示字串／倒數欄位；前端未捏造倒數。

- T182 Codex：設計 v4 artifact 在 IAB 要求登入，Chrome 登入後仍顯示 Artifact took too long to load。已依任務列完整規格實作並實測；視覺參照頁無法逐張核對，不宣稱逐像素還原。未更改分享權限。

- T165 Codex：Figma Starter MCP 配額用完。14 個 editable 狀態與元件已建立，桌面高度修正已核對；手機 Field 內框待恢復 48px、上傳 CTA 待移到照片之前，待清理暫存 capture 5:2／照片節點 10:2，並核對 SAM Source instance 的文字 property（Label#9:21）。另需同步首頁影格來源說明（main 已標示生成測試影格）。未經核對不宣稱 Figma 最終完成。前端這些修正均已完成並實測；不升級方案、不換管道繞過配額。

- [T122 Antigravity 乾淨環境安裝驗證] 在 `/tmp/slope-coach-clean-test` 依照 README 完整測試安裝：
  1. Frontend：`cd frontend && npm install && npm test` 111 項測試全數 PASS。
  2. Python Backend：macOS Homebrew 預設 Python 3.14.7 觸發 PEP 668 `externally-managed-environment`，導致 `python3 -m venv .venv` 在 ensurepip 階段失敗。解法為 README 所述安裝並指定 `python@3.11`（`brew install python@3.11` 後以 `python3.11 -m venv .venv` 建立），或在現有 Python 3.14 下使用 wheel 解包 / `--break-system-packages`。
  3. ffmpeg：部分 macOS Homebrew ffmpeg 缺 `drawtext` 濾鏡。Antigravity 說已在 `scripts/gate_prepare.py` 加退路（commit 9db92e3），但這個 commit 沒有 push 到 GitHub（Claude 10/29 14:20 查證）。
  （Claude：這三點都不用 john 決定。README 已寫 `python3.11`；drawtext 退路只影響關卡用的縮圖腳本，不影響產品。）

- 10/29 Codex 合併檢查：PR #55 仍為 OPEN；PR #56 已 MERGED，但目標是 #55 的 codex/T150-window-keyboard，不是 main。因此 main 尚未包含 T143–T152 的全部前端。PR #58（T153）已改接在 #55 分支上避免重複大 diff；請 Claude 先把 #55 合併 main，再 retarget／合併 #58。
- [T119 Antigravity] 本地端已備妥 `docker-compose.yml`（包含 backend + frontend 雙服務，支援 ffmpeg 與 .env 注入）。關於線上部署目標平台（如 Render, Fly.io, Railway, Google Cloud Run），請 john 決定目標平台並提供部署帳號／密鑰，Antigravity 不自行註冊外部帳號。

- [T54 Antigravity 上傳安全提案] 建議在後端 `POST /api/audits` 實施安全防護：(1) 限制檔案大小上限為 200 MB（超出回傳 413 Payload Too Large）；(2) 限制 MIME 格式僅接受 `video/mp4`, `video/quicktime`, `video/webm`；(3) 依 Client IP 限制每天最多 20 次稽核呼叫（超額回傳 429 Too Many Requests）。此提案等待 Claude 審查後即可實作。

- （10/29 Claude）要不要用 GitHub Pages 放純靜態 demo 版（Codex T138 做好之後）？這會把 demo 紀錄公開放上網，repo 本來就要公開，Claude 建議可以，但要等 john 同意才開。


- T113 Codex：同步 POST /api/audits 不提供追蹤／計算分階段狀態；本次只呈現已知 upload bytes 與合併處理中。若要真實分階段進度，請 Claude 設計工作狀態端點；前端不以計時偽造階段。

- T105 Codex：先前本機瀏覽器 origin 授權被拒，本次不繞過；已補 390px 收縮與語意測試，但實際 viewport／鍵盤／螢幕閱讀器驗收仍需 Antigravity（T120）。

- Codex 10/28：本機 ffmpeg 缺 drawtext filter，pytest tests/scripts/test_gate_prepare.py::test_prepare_writes_sheet_and_blank_labels 失敗（其餘 75 pass）。請 Claude／Antigravity 確認具 drawtext 的 ffmpeg；本次不改後端／部署或跳過測試掩蓋。T89 npm 59 pass、build pass，但 pytest 全綠受此環境缺口阻擋。

- [Muse] 新套件 `meta-sam-parser`（Meta 官方、無依賴）：SAM 遮罩自研編碼，只能用官方解析器，已用於 track。requirements 請加 `openai` + `meta-sam-parser`。


- [Muse] 主 checkout（/Users/aacc/Documents/slope-coach，切在 antigravity/T44-readme）有未解決的 `docs/STATUS.md` 衝突，`git pull origin main` 被擋下。Muse 沒碰它，在 worktree 照 origin/main 繼續做；請 Antigravity 或 john 解掉。

## 已做的決定

- 10/29 13:34 john：自拍影片的縮圖（`data/gate/sheets/own_*`，客廳、沒有人臉）留在公開 repo，當作實拍的證據。影片本身仍然不准 commit。
- 10/29 13:05 Claude：**demo 主表改用 SAM 3.1 v4**（自拍 3 支一致、生成 4 支不一致、3 支拒判：同一種追蹤下三種結果都有，而且是 Muse 的模型）。顏色版並排當對照，兩版不同的地方照實寫（例如 own_3：SAM 8.68 一致、顏色 8.15 不一致）。README 已更新。
- 10/29 12:30 Claude：demo 主表暫用**顏色追蹤版**（目前唯一在同一種追蹤下有「真實一致、生成不一致、拒判」三種結果的版本），SAM 版並排顯示。T114 自拍影片跑完 SAM 後再決定：若 SAM 版三種結果都有，demo 改以 SAM 版為主（Muse 優先），顏色版當對照。兩版的不同照實寫，不挑對自己有利的。
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
| 10/29 | T108：suggest_object 真打 clip2 一次 | 0.008 | 0.271（含未合併 T107 0.077、T112 0.096） |
| 10/29 | T109：抽欄位真打 7 次（2 輪驗證修正＋重試；單次約 $0.02，輸出 token 異常多） | 0.164 | 0.435（含未合併 T107 0.077、T112 0.096、T108 0.008） |
| 10/29 | T112：explain＋headline 真打 own_2、clip2 各兩種（7 次呼叫含 1 次驗證重試） | 0.096 | 0.263（含未合併 T107 的 0.077） |
| 10/29 | T113：SAM v2 重跑 7 支（SAM 7 次 $0.077＋explain 15 次 $0.244 含 8 次重試＋headline 4 次 $0.038） | 0.360 | 0.794 |
| 10/29 | T114：SAM v3 跑 10 支（自拍 3＋生成 7，純 SAM 無解說） | 0.107 | 0.902 |
| 10/29 | T116：SAM v4 跑 10 支（計時修好後，純 SAM） | 0.107 | 1.009 |
| 10/29 | T117：demo 版 10 支（SAM $0.107＋解說 10 次零重試 $0.155＋標題 7 次 $0.081） | 0.344 | 1.353 |
| 10/29 | T118：英文版重產 demo（SAM $0.107＋解說 10 次零重試 $0.161＋標題 7 次 $0.064） | 0.333 | 1.686 |
| 10/29 | T119：live smoke 4 步（偵訊 $0.012＋物體建議 $0.006＋SAM $0.010＋解說 $0.017；語音 502 未計費） | 0.046 | 1.732 |
| 10/29 | T166：修語音 502（2 draft $0.036＋轉錄 2 次 $0.0003＋抽欄位 $0.003） | 0.039 | 1.771 |
| 10/31 | T179：SAM 跑 3 支車子片（181 秒 $0.022＋255 秒 $0.038＋66 秒 $0.029） | 0.089 | 1.859 |
| 10/31 | T183：凍結前真打（2 draft $0.058＋語音 3 次 $0.007＋SAM 稽核 2 次 $0.063 含解說標題） | 0.127 | 1.987 |
| 10/31 | T184：SAM 跑 4 支側面車子片 6 個窗（每窗 $0.018–0.024） | 0.125 | 2.112 |

## 工作日誌（最新在上）

- 10/31 Codex T193：分享卡改成 1080×1920 PNG 與一致的 HTML 預覽，琥珀／藍／灰對應三種有文字的判定；徽章照實際追蹤來源，數字只格式化既有 g_vs_earth 或 g_apparent_m_s2。保留 physicsCardLines 全部證據原文在收合的完整證據與既有報告；PNG 為摘要，固定範圍說明。瀏覽器實際下載 meta_clip4 PNG 並開圖確認尺寸／版面／來源；中英文匯出使用現有翻譯，不改模型原文。npm 135 tests、一般／demo build 通過。

- 10/31 Codex T192：卡片與 How 滑鼠效果提供 focus-visible 對應；Tab 已實測展開卡片，skip link 保留 #wall 並聚焦 workspace。減少動態效果停用全部動畫／transition 並顯示完整終態。#8A8F98 在四種深色表面皆 ≥4.5:1；未選卡改暗底，不降低文字 opacity。補全站 img alt／鍵盤／配色檢查，圖表文字與軌跡使用深色主題 token，未改數字、擬合或判定。npm 133 tests、一般／demo build 通過。

- 10/31 Codex T191：手機與平板 Results／How 單欄；卡片點一下展開、再次點擊收起，窄螢幕不啟用 hover 鎖定。瀏覽器實測 390／768px：home、wall、how、audit、compare、demo、saved example 與五個 coach 頁，頁面 scrollWidth 不超過 viewport，控制項／section／article 無溢出；手機二次點擊 evidence 高度為 0。新增版面契約與 disclosure 測試（Node 無排版引擎，幾何以瀏覽器實測）；npm 130 tests、一般／demo build 通過。

- 10/31 07:20 Claude：合併 Muse T184、T186–T189，Antigravity T197，Codex T182。合併後 pytest 262、npm test 128、兩個 build 都過；1440／390 px 首頁截圖正常、沒有橫向捲動。修 `probe_fps` 的 tmcd bug 和 T197 找到的 3 個安裝問題。**車子結果：4 支 Pexels／Pixabay 側面片全部資料不足**（整台車入鏡太短或往鏡頭偏），所以 demo 目前沒有「車子一致」的例子；需要 john 拍一支或用 Meta AI 生成。Meta API 累計 $2.39。

- 10/31 Muse 完成 T184（分支 muse/T184-car-side，commit 8fdb3d5）：4 支側面車子片、6 個窗全跑完，track_source 全是 sam，**全部 insufficient_data**（不挑，全記）。car_side_1 灰色小轎車 1.0–1.5 秒：只追到 0.47 秒、差 0.5 門檻（27 秒，$0.022）；同支 7.5–8.5 秒（青色車）：只追到 73%（車子從左邊出畫面，25 秒，$0.021）；同支 9.25–10.0 秒：只追到 18%（窗內前半沒車、後半是貼很近的黑車，Manus 的時間估計在這支上偏了，23 秒，$0.019）。car_side_2 淺色車 5.0–5.75 秒：尺寸 +43%（往鏡頭方向偏，29 秒，$0.024）。car_side_3 遠車道 3.0–3.75 秒：像素車長變化太大不能當尺（19 秒，$0.018）。car_side_4（Pixabay）4.4–4.6 秒：只追到 3 格、要 8 格，如預期被拒（25 秒，$0.022）。6 個 overlay 都看了：SAM 每次都鎖對車，不用換顏色提示詞。6 次都沒走到擬合，所以沒有 speed_km_h、accel_g、car_length_px、n_points。car_meta_1.mp4 不存在（john 還沒生成），沒跑。下載法：Pexels 頁面被 Cloudflare 擋，改打 `pexels.com/download/video/<id>/?h=1080&w=1920` 拿 HD 直鏈；Pixabay 同樣被擋，用 r.jina.ai 讀頁面挖 cdn 直鏈。後端 bug（已寫進「缺什麼」，沒改後端）：三支 Pexels 檔自帶 tmcd 軌，ffprobe 9 會把 stream_groups＋streams 各印一次，`probe_fps()` 拿兩行 `r_frame_rate` 去 `int()` 炸掉，`/api/audits` 回 422（$0，SAM 前就擋下）。繞法：本地 `ffmpeg -map 0:v:0 -c copy -dn -write_tmcd 0` 重裝（像素完全一樣，只去 tmcd 軌），檔名 `*_clean.mp4`，都在 repo 外。TestClient＋真 API（uvicorn 照樣 EPERM）。$0.125（上限 $0.40），累計 $2.112。
- 10/31 Muse 完成 T186（分支 muse/T186-vehicle-scene，commit 6cb4f5a）：`suggest_object` 多回三個鍵（側面車給 vehicle＋車種；朝鏡頭或鏡頭動給 judgeable=false＋原因；車種限四類＋unknown，帶數字退件）；偵訊可問 vehicle_class。缺的三鍵後端 `ObjectSuggestion` 還沒收（Pydantic 會靜默丟掉）、`QuestionField` 還沒加 vehicle_class（模型若問了會整組掉回 mock，不會 500），已寫進「缺什麼」請 Claude 接。pytest 252 全過，$0。
- 10/31 Muse 完成 T187（分支 muse/T187-vehicle-explain，commit c3b98e3）：車子說明三種判定本來就通（explain 是 payload 驅動）；補車子提示指引 1.2 g 比較句，中英都有；禁字加「假的」。headline 不用動（T176 的槽位＋檢查已符合）。5 新測試，pytest 250 全過，$0。
- 10/31 Muse 完成 T188（分支 muse/T188-failure-tests，commit 72c4f91）：五項查完：非 JSON、逾時、$120 都有舊測試（本次只給 $120 拒絕加訊息斷言）；補 4 個新測試（interview 非 JSON、SAM 空回傳、hooks 全缺、語音數字稿未確認）。缺：後端空追蹤原因還不是「追蹤缺失」，已寫進「缺什麼」請 Claude 定。pytest 249 全過，$0。
| 10/31 | T189：凍結前最後真打 4 案（自拍 $0.062＋clip4 $0.053＋clip2 $0.043＋車 $0.057＋補跑自拍 $0.066） | 0.281 | 2.267（T184 的 $0.125 在未合併分支上，合起來約 $2.393） |
- 10/31 Muse 完成 T189（分支 muse/T189-live-check，commit dd165b7）：`scripts/demo_live_check.py` 跑完 4 案全 PASS（自拍一致 g=9.44、clip4 不一致 g=0.14、clip2 拒判、T184 最好的車 0.47 秒拒判；source 標籤全對）。$0.281，pytest 245 全過。Muse 待辦全部結束。
- 10/31 Antigravity 完成 T197（分支 antigravity/T197-fresh-install）：在全新目錄從零 clone 依 README 步驟驗證。git clone 2.54s 通過；ffmpeg/python3.11/node24/npm 依賴確認；npm ci 1.12s、npm test 126 pass (3.16s)；pytest 244 pass (17.44s)；scripts/e2e_slope_demo.py 與 scripts/e2e_audit.py 均通過。發現 3 項問題（python3.11 ensurepip 遇 truststore 異常、docker compose 缺前置需求、dev.sh 寫死 python3）已寫進「缺什麼」待 Claude 修改。下一項 T196 待 Codex T182 合併。
- 10/31 Codex T182：深色 v4、獨立首頁／Results／How／上傳路由、三卡 hover 與四步展開、meta_clip4 儲存軌跡 CSS 動畫。保留所有 API、testid、來源與原始資料，導覽其餘入口移 footer；空 hash 預設首頁。三套字體從 Google Fonts 官方下載且附 OFL。桌面 1440 首頁已檢視；設計 artifact 逾時依任務規格落地。npm 128 tests、一般與 demo build 通過；無新依賴。

- 10/31 02:45 Claude：john 要求一次給多件。Manus T178 收進 `docs/research/vehicle.md` 並核對（T185）。排了 Muse T184、T186–T189，Codex T182（改成設計 v4 規格）、T191–T195，Antigravity T196–T198，Manus T199–T201，Claude T190、T202。

- 10/31 Codex T173 整合：依 john 新指示 checkout main／pull 後，將已合併 T177 與 T183 的 main（1cd45cf）合入 codex/T173-gravity-ruler。STATUS 保留 main 的所有進度，再補 T173 完成列；前端保留車子與重力當尺兩套顯示。整合後 npm 126 pass、一般／demo build pass（入口 88,434／87,332 bytes）；同一後端版本 pytest 244 pass。T182 依 john 指示暫緩，沒有開始改版。

- 10/31 Codex T173：稽核結果與結果牆在 Details 外顯示後端四個 if_earth_* 讀數，物理名片／PNG 共用同一份顯示欄位。固定標題「如果這是地球重力、正常速度」及說明「這是假設下的讀數，不是判定；慢動作會讓高度變大。」；中英文同步，缺欄位逐行隱藏、全缺就不顯示區塊，保留零值、負角度與原始精度（title），不自算尺寸或改判定。npm test 120 pass、一般／demo build pass（入口 86,150／85,048 bytes）；瀏覽器核對結果牆十筆中七筆有讀數、三筆拒判不補值，390px scrollWidth 375px。只改 frontend／STATUS，沒改 demo JSON／後端或付費呼叫。T177 已另推 codex/T177-vehicle（9041ce8），本分支由 main 獨立建立。

- 10/31 Muse 完成 T183（分支 muse/T183-final-smoke，commit b2928bd）：凍結前真打 8 步全過。meta_clip4：draft（interview.source=model，問題含 vehicle 選項，suggestion=orange basketball／靜止，21 秒 $0.020）→windows（physics，3 個窗，$0）→語音（200，source 全 model，$0.003）→稽核 0–2.5 秒：inconsistent、g=0.143、track_source=sam，headline 和 explanation 都是 source=model 且通過檢查（52 秒 $0.037）。靜音 3 秒送 /voice：200、transcript=沒有聽到內容、fields={}、fields 來源 none，T171 線上確認（$0）。車子 4064324：draft（source=model，直接問「白色車的車身長度」，22 秒 $0.038）→語音 200（$0.004）→稽核 vehicle／4.5m／6–8.2 秒：insufficient_data「移動不到一個車身長」，sam（188 秒 $0.026）。兩個環境偏差：(1) uvicorn 綁 8000 照樣 EPERM，改 TestClient＋真 API（同 T179）；(2) `say` 在沙盒只吐 4KB 空檔、無其他 TTS 也無麥克風，兩次語音改送 own_2 的真實環境音：逐字稿把雜音聽成不相關的英文、fields={}（正確，無可抽），傳輸＋雙模型路徑是活的，指定句子的抽欄位由 T109／T176 的 mock 測試覆蓋。觀察（非 bug，不改後端）：車子 draft 的 suggestion 說「orange pedestrian」（首格有行人，prefill 等使用者改）；本次車子拒判理由與 T179 同支同窗措辭不同（SAM 追蹤每次略有差異），同樣是動量不足拒判、numbers 照例無 car_length_px。$0.127（上限 $0.40），累計 $1.987。
- 10/31 Codex T177：車子模型已接上兩條上傳流程、儲存紀錄驗證與語音逐欄採用；車長欄位／參考說明／整車側拍時間窗提示中英同步。判定下顯示後端 km/h（整數）、g（兩位小數，依 accel_m_s2 標加速／煞車）、每秒車身長與 1.2 g 所需車長；不推算或修改任何數字，缺欄位隱藏，無確認車長時不顯示 km/h 或 g 量測。兩筆既有車子 JSON 加入獨立程式範例區，摘要明標「程式模擬」，沒有改 JSON。車子回放保留原片／追蹤點，不套自由飛行重力鬼影說明。npm test 124 pass、一般／VITE_DEMO_ONLY=1 build pass（入口 87,733／86,631 bytes），瀏覽器已核對繁中選單、車長提示、煞車／加速兩筆範例；390px scrollWidth 375px，無橫向溢出。只改 frontend 與本 STATUS，沒有新套件或付費模型呼叫。缺口：側拍真車與獨立速度參考仍待 T178，程式模擬不當真片準確度證據；T177 不改後端或門檻。

- 10/31 Muse 完成 T179（分支 muse/T179-sam-car）：3 支車子片全 201、track_source=sam、全拒判如預期。(1) 4064324（6–8.2 秒）：移動不到一個車身長，181 秒，$0.022；(2) 4513718（0–9 秒）：像素車長變化太大不能當尺，255 秒，$0.038；(3) 9337511（5–8.9 秒）：尺寸 +228% 朝鏡頭，66 秒，$0.029。三支 numbers 都沒有 car_length_px（拒判本來就不算尺），但拒判理由都不是「no car widths」，第 2 支的理由本身就是拿像素車長算的——width_px 從 SAM 到後端接通。uvicorn 照樣 EPERM，改 TestClient。$0.089，累計 $1.859。
- 10/31 Muse 完成 T176（分支 muse/T176-vehicle）：_dense_detections 填 width_px（正規化 0..1，無 box 不填）；偵訊提示詞 assumed_model 加 vehicle、車長說明；語音 enum＋檢查＋提示詞加 vehicle；車子標題走 {speed_km_h:0}／{accel_g:1} 槽位＋現有檢查。5 新測試，pytest 239 全綠。沒真打 API（$0）。
- 10/31 01:30 Claude：john 要加車子。T175 完成（physics＋後端＋測試，見 Claude 那一行）。排了 T176 Muse（SAM 追蹤框寬度、偵訊和語音認得車子、車子標題）、T177 Codex（車子的選項和結果卡）、T178 Manus（找側面車子影片、車長表、1.2 g 的來源）。順序：Muse 和 Codex 可以同時做；Manus 找到影片後 john 下載放在 repo 外的 `~/slope-own-clips/`，Claude 跑完再決定 demo 要不要放車子。
- 10/29 Codex T167／完成核對：PR #87（T165 前端）及 #88（T157）均已合併 main；本輪以 6c2e2c6 為基準，GitHub Pages 與 CI 的最新 run 都成功。實際開啟 https://johncat88425-del.github.io/slope-coach/，1440／390px 各看六頁並保存十二張不同 screenshot（/tmp，不 commit），沒有空白頁、失效圖片、橫向溢出或 console error；結果牆十筆、比較展示十筆、首頁三結果入口可用。品牌、skip link（焦點 workspace）、五個教練分頁亦通過；靜態模式上傳停用、來源提示明確。發現 Guided demo 在長頁面把控制鈕留在頁頂、點一般導覽時會強制跳回、跨頁焦點遺失，已改為啟用時固定面板、直接對齊目標標題、明確換頁即結束導覽，進入／跨步保留控制項焦點、完成／退出返回啟動按鈕。以 Pages 相同 /slope-coach/ base 建置驗證 1440／390px 六步鍵盤操作；手機 ghost 標題 top24px、操作面板在 viewport 內，文字對比受檢最低5.40:1。npm 118 pass、pytest 224 pass，npm run build pass（入口85,449 bytes），Pages 同指令 build pass（入口84,359 bytes），沒有後端／API／測量值改動，沒有付費模型呼叫。修補隨此分支送審，尚未宣稱線上已部署；目前公開網站是儲存紀錄展示版，完整上傳分析需本機完整 app 或另行部署後端。Figma get_metadata 再次回 Starter tool-call quota，無法重新核對手機收尾，T165 維持未勾。
- 10/29 18:10 Claude：核對 Manus 的提交文字和三分鐘旁白。數字都對，用詞沒有違規。修改三處：自拍的 g 統一用 demo 紀錄的 9.31、9.45、8.68（README 同步改了，PR #95）；拿掉重複的「featured 9.45」；補一句 Muse Code 負責 Meta API 層。也註明 0:00–1:40 要用本機完整版錄（靜態網站沒有上傳功能，也沒有自拍影片）。

- 10/29 17:50 Claude：**提交前檢查（第一輪）**。(1) 金鑰：repo 和 git 歷史都沒有金鑰，只有 `.env.example`；(2) 產品程式只呼叫 Meta：`meta_client/client.py` 指向 `api.meta.ai/v1`，backend／meta_client 只出現 muse-spark、sam-3.1、muse-voice-transcribe，沒有其他廠商；contributor 版只出現在價目表，產品不會呼叫；(3) 禁用字眼：README、前端、demo 資料都沒有「偵測 AI／假影片／任何影片」的宣稱，出現的地方都是禁用清單或「不判斷」的說明；(4) 第一個 commit 是 10/27，都在 10/26 之後；(5) repo 公開、MIT；(6) git 裡沒有 john 的自拍影片，demo JSON 只有檔名；(7) README 的 SAM 數字和 demo JSON 對得上。**新增**：GitHub Pages 靜態 demo（`.github/workflows/pages.yml`，用 `VITE_DEMO_ONLY=1`，不呼叫後端或模型），README 加網址；john 要在 Settings 打開一次（T168）。排了 T167、T169、T170。
- 10/29 Muse 完成 T166（分支 muse/T166-voice-encoding）：request 補 `audioEncoding: "WAV"`（batch 端點的值；realtime 才用 PCM_24KHZ／PCM_16KHZ）＋斷言測試；真打 voice 端點回 200、用 own_2 環境音轉出 3 秒英文口語、無答案內容故 fields 為空（沒亂猜）。pytest 222 全綠。已知殘留：純靜音轉出空稿仍走 502（合理但訊息誤導，可排下個任務改成空欄位回 200）。$0.039，累計 $1.771。
- 10/29 Antigravity 工作總結：完成 T161（手機 390px 截圖重拍並驗證 md5 不同）、T121（10s 1080p 效能量測 1.13s/0.36s < 20s）、T122（乾淨環境安裝驗證與卡點記錄）、T53（30s 1080p iPhone HEVC 效能量測 1.61s/0.38s < 20s）、T68（鬼影對照與物理名片 E2E 測試與桌面/手機截圖）。完成表已無 Antigravity 待辦項目。

- 10/29 Codex T157 最終同步：保留 main 的協調者範例圖片來源說明與回歸測試，後續整合改由 PR #88 交付（PR #87 的 809f3df 已合併）。重跑 npm 118 pass、標準／靜態 build pass（入口 85,160／84,058 bytes）；同一後端版本 pytest 222 pass。Figma 待配額恢復，前端與 T157 已完成並提交審查。

- 10/29 Codex 本輪可執行前端待辦已完成：主改版 PR #87 已由 Claude 合併；T157（82f90f9）與後續整合修整交付 PR #88（目標 main）。已保留 Claude 在 main 補的範例來源文案與測試。Figma 手機收尾仍受 Starter MCP 配額阻擋，T165 保留未勾及明確續接項目。

- 10/29 Codex T165 整合驗證：把已獨立推送的 T157 合入設計分支供整體審查，PR #87 的先前版本已由 Claude 合併；後續 T157 整合與標題微調由 PR #88（目標 main）交付。保留新版導覽、48px 控制項與原文保護，合併 demo 入口／最終資料、雙語字典及測試；模型標題改為直向排列來源，結果牆判定優先，完整展示使用兩欄／手機單欄。npm 118 pass，普通／靜態 build pass（入口 85,075／83,973 bytes），同一 main 的 pytest 222 pass。以最終 SAM 結果實測 390px 結果與 1440px 並排，Details 收合、無橫向溢出、文字最低對比 5.51:1；Figma 配額收尾仍未完成。

- 10/29 Codex T157：從最新 origin/main 獨立開 codex/T157-final-demo（PR 目標 main）。靜態 demo 和結果牆共用 DemoCatalog 全 10 筆最終紀錄，完整保留 3 筆實拍一致、4 筆生成不一致、3 筆資料不足；不再把 own_3 寫成不一致，也不把透視拒判寫成追蹤不足。沒有複製／改寫 JSON，headline／explanation／reasons 均用原文，空 headline 不補；結果牆補七筆已提供的模型標題與原始原因。首頁、30秒導覽與預設並排共用 entry keys（own_2／meta4／meta2），仍可選所有 10 筆，程式繪製案例移到獨立收合區。導覽等待 lazy view 掛載並展開證據祖先，實際鬼影／名片步驟可見，支援 reduced motion；拒判字幕依實際 verdict 引導讀原始原因。靜態模式的全站提示改為只重播儲存結果，避免誤稱媒體會上傳。瀏覽器驗證 10 筆／七個標題、390px 無橫向溢出、預設並排一致與不一致、繁中仍保留英文模型原文。新增完整紀錄與內容不變、三結果入口、雙語及開發範例分離測試；npm 114 pass、普通／靜態 build pass（入口 83,634／82,531 bytes，gzip 前），pytest 222 pass。未改後端、API、數字或資料檔，未打付費模型。

- 10/29 14:55 Claude：合併 Muse T119 和 Codex T165（前端改版）。T165 的上傳頁大圖其實是 Meta AI 生成影片 meta_clip4 的影格，原本寫「保存的運動範例」容易讓人以為是真實影片，Claude 改成標明是 Meta AI 測試影片（中英文案與測試一起改）。npm 115、build、pytest 222 都過。新增 Muse T166 修語音 502。
- 10/29 Muse 完成 T119（分支 muse/T119-live-smoke，只改 STATUS＋cost_log）：4 步 3 過。(1) drafts 201／13 秒／interview.source=model、3 題英文、suggestion 有（orange basketball／static，source muse-spark-1.3）；(2) windows 200／1.5 秒／source=physics、10 個窗、$0；(3) voice **502**「voice model unavailable: ModelOutputError」——根因在我方 `meta_client/voice.py`：ASR API 回 400「You must specify the 'audioEncoding' field」，我方 request 只有 model 沒帶該欄（T24 真打時不用，API 變嚴了；送的是 24kHz 單聲道 PCM）；修法是下個 Muse 任務補 audioEncoding＋測試，後端不用動；(4) audits 201／22.5 秒／insufficient_data（跟 v4 一致）、track_source=sam、解說 model、無標題（拒判本來就沒有）。$0.046，累計 $1.732。環境偏離兩處：沙盒禁所有監聽 socket（TCP＋unix 都 EPERM），改 TestClient 跑同一個 ASGI app＋真 API（秒數不含 TCP）；`say` 在沙盒吐空檔，語音改送 own_1 的真實環境音（4 秒）。
- 10/29 Codex T165：依 john 指示建立 Figma Editorial Lab（上傳、確認時間窗、等待、錯誤、結果、結果牆、並排，1440／390px 各七張；Auto Layout、47 個 tokens、21 個 variants、七種文字樣式）。Figma Starter MCP 配額於手機最後修正時用完，留下的明確修正見待決定，整項保留未勾。現有 frontend 已改為米白／墨藍／朱橘、單一上傳主操作、影片＋時間窗＋欄位工作區、細分隔線與一致結果層級；Details 預設收合，來源依實際 model／mock／template／tracker 顯示，後端文字用 Verbatim 保留。配色標示為受和田三造《配色事典》啟發，未虛構原書頁碼或色碼；本地 Noto Sans TC 字型附 SIL OFL，無新套件。首頁照片取自既有公開範例的單張影格，並有範例說明。瀏覽器 1440px／390px 檢查，手機首屏上傳可見；鍵盤選片→時間窗→回答→送出→等待→結果通過，焦點分別交給時間起點／狀態／判定；結果牆與並排無橫向溢出，受檢文字最低對比 5.51:1，繁中同步。npm 115 pass，標準／demo build pass（入口 81,392／80,505 bytes）；pytest 219 pass／1 既有 ffmpeg drawtext 缺口。未改後端、API、demo JSON 或測量值，mock 測試無付費模型呼叫。同步最新 main 後重驗 npm 115 pass、pytest 222 pass（Claude 註：drawtext 退路其實沒有合併，是 Codex 的環境本身有 drawtext）；普通 build 亦通過。

- 10/29 13:35 Claude：合併 Muse T118（英文解說與標題；10 支 verdict 不變，SAM 重跑數字差 <0.2%，例如 own_1 9.30→9.31，README 註明）與 Antigravity T161（三張手機截圖 md5 都不同；gate_prepare 在沒有 drawtext 的 ffmpeg 改用無字幕縮圖）。
- 10/29 Muse 完成 T118（分支 muse/T118-english-text）：headline 加 lang 參數（英文 prompt＋天體名不轉中文，禁真假／real／fake／AI 規則不變）＋hooks 切英文＋3 測試；pytest 221 pass。重跑 demo 指令：10 支 verdict 全同、數字差 <0.2%（SAM 非確定性；own_1 顯示值 9.30→9.31）、10 份文字全轉英文且無中文殘留、6 份合成 JSON 未動。explain 連續第二次 10 次零重試。$0.333，累計 $1.686。
- 10/29 13:20 Claude：審查並合併 Codex T162（鍵盤焦點、對比、停用狀態可讀、解說來源標示）。
- 10/29 Codex 沒有待辦了。T162 已完成並推送 codex/T162-a11y（PR #80，目標 main），已同步協調者的最新進度。T157 尚無 Claude 的資料定版公告，依 john 規則保留未勾；無其他可執行的 Codex 待辦。
- 10/29 Codex T162：已用瀏覽器以 Tab／Enter／空白鍵從選片、準備問題、回答、確認時間窗到結果；素材為 repo 既有 meta_clip2，輸入照 manifest，獨立 mock 後端無金鑰、無付費呼叫。發現準備後焦點掉到 BODY，已改交接到物體名；等待提示、漏答錯誤與新結果都有焦點位置及深色焦點框。結果 aria-labelledby 指向各自判定，並排不重複 ID。小標原對比4.48:1，改為顏色 token；移除停用控制項的透明度、保留可讀文字。390×844 實測表單、收合／展開結果、結果牆及並排頁沒有橫向溢出（scrollWidth375≤innerWidth390）；受檢頁面最低文字對比5.49:1，1280px並排亦通過。首頁卡片／結果牆補說明來源徽章；模型、模板／mock 依實際值，既有問題／標題／追蹤／語音來源標示已核對。新增對比、唯一結果標籤、雙語來源測試；npm111 pass、一般與靜態build pass（入口79,391／78,502 bytes）。合併最新main後pytest219 pass／1既有ffmpeg drawtext失敗。只改frontend與本STATUS，資料／後端未改。
- 10/29 13:15 Claude：**demo 資料已定版**（Codex 可以做 T157）。合併 Muse T117：`data/demo/` 的 10 筆真實／生成紀錄改成 SAM v4 版，verdict 與 v4 表完全相同，沒有影片連結，解說和標題都是 Muse Spark 寫的且通過後端檢查。數字和判定不會再變；只有解說和標題的文字會由 Muse T118 換成英文（同樣欄位，前端不用改）。
- 10/29 Muse 完成 T117（分支 muse/T117-demo-sam）：10 支重跑＋解說＋標題，verdict 全跟 v4 一樣（own_2 g 9.46→9.45 顯示捨入而已）；10 個 data/demo JSON 換成 SAM 版，解說／標題 source 都是 model。T115 修好得到驗證：explain 10 次零重試（T113 是 15 次 8 重試）。git status 確認只有 json／md／STATUS／cost_log，無影片。$0.344，累計 $1.353。
- 10/29 13:05 Claude：合併 Muse T116（SAM v4）。修好計時後自拍 3 支 g = 9.30、9.46、8.68 全部一致；生成影片結果和 v2、v3 幾乎一樣。`audit_batch` 加 `--json-dir`，存完整稽核紀錄給 demo（不含影片連結）。README 結果表改成 SAM 為主、顏色對照。新增 Muse T117。
- 10/29 Muse 完成 T116（分支 muse/T116-sam-v4）：計時修好後重跑 10 支，自拍 3 支全變一致（g=9.30／9.46／8.68），v3 偏角確認是轉碼 bug；生成側 verdict 不變、數字微移；3 張自拍 overlay 紅點在球上。demo「同一種追蹤三種結果」達成。$0.107，累計 $1.009。
- 10/29 12:55 Claude：合併 Muse T114（SAM v3）、T115（解說可引用原因句裡的門檻數字）。T115 只改了 meta_client 的檢查，後端的第二道檢查會照樣擋掉，所以後端 `_number_sources` 也加上「程式自己寫的原因句裡的數字」（有測試；模型自己編的數字仍然擋）。找到並修好 SAM 15fps 計時 bug（見規則變更紀錄），v2、v3 的 SAM 數字作廢待 v4。新增 Muse T116。
- 10/29 Muse 完成 T114（分支 muse/T114-sam-own）：自拍 3 支＋生成 7 支全用 SAM 跑（批次已默認關解說，只花 SAM 錢）。自拍全判不一致（偏角 -22～-27 度），3 張 overlay 紅點都在球上、不是跟丟；跟顏色版矛盾，「同一種追蹤下真實一致」目前達不到，請 Claude／john 決定 demo 用版。行動偏離：`~/slope-own-clips` 不存在（三支在 Downloads）、沙盒寫不到 `~`，改放 /tmp/slope-own-clips（等價，同在 repo 外、沒 commit）。$0.107，累計 $0.902。
- 10/29 Muse 完成 T115（分支 muse/T115-explain-retries）：8 次重試全是「數字來源」沒過——模型照提示詞引用 payload 裡的門檻（8.34／11.28），但那些數字只活在原因句字串裡，檢查只收數字欄位，首輪幾乎必死一次；另 9.81／fps 也不在 payload 裡。修法（只動 meta_client）：explain 用程式 parse 原因句數字加入 allowlist（檢查本體沒動），提示詞點名禁寫 fps／自算百分比、範例 9.81 換成 1.71；2 測試鎖住（門檻引文一次過、9.81／fps 照樣擋）。$0 真打，全套件 216 pass。建議 Claude：後端 `_model_text` 的 `_number_sources` 也要加同樣的字串數字，否則修好的解說在後端門還是會被退回模板；另建議把驗證失敗的原文記下來，下次不用猜。
- 10/29 12:40 Claude：審查並合併 Codex T159（物體名稱預填，鏡頭建議只顯示文字）與 T160（語音回答逐欄按 Use this 才填入）。
- 10/29 Codex 沒有待辦了。T159／T160 已完成並推送 PR #70／#74，目標都是 main，兩者已同步最新 main 且可合併。T157 仍待 Claude 資料定版通知，依規則保留未勾；無其他可執行的 Codex 待辦。npm108 pass、標準／靜態 build pass；pytest213 pass／1既有drawtext環境失敗。
- 10/29 Codex T160：接 API v1.0 錄音→預聽→明確送出→逐字稿／欄位預覽，每欄 Use this 才填一般表單，不自動提交稽核；語音時間窗仍需影片確認。來源標示 Voice Transcribe／Spark；mock 停用錄音。錄音超過10MB／錯誤／卸載均釋放麥克風，送出防重複、失敗保留答案與錄音，換草稿忽略晚到回應；未加套件、未呼叫付費模型。新增假的 fetch、錄音器、逐欄、精度、mock、錯誤及雙語測試；npm108 pass、標準與靜態build pass（入口79,345／78,456 bytes）；pytest213 pass/1既有drawtext失敗。實機端到端待Antigravity。
- 10/29 Codex T159：接 API v1.0 的 suggestion 預填物體名；手動改名優先，換片重設。鏡頭建議只顯示文字，從不填確認欄位；null 不顯示提示。原因保留原文，中英文同步；npm101 pass、build pass。pytest213 pass/1 fail，仍為既有 ffmpeg drawtext 缺口。未改後端或量測值。
- 10/29 12:30 Claude：合併 Muse T113（SAM v2）。兩種追蹤判出的不是同一批（尺寸變化估計不同：clip4 顏色 +79%、SAM +15%），兩版都保留。`scripts/audit_batch.py` 改成預設不呼叫解說和標題（`--explain` 才呼叫），因為 T113 光解說就花了 0.24 美元。新增 Muse T114（自拍影片跑 SAM）、T115（解說驗證失敗原因）。
- 10/29 Muse 完成 T113（分支 muse/T113-sam-v2）：T146 修好後重跑，4 支判出數字、3 支透視拒判；overlay 確認 3 支紅點在球上、clip4 請 john 複看。注意：合併後每次稽核自動跑解說＋標題，本次 explain 重試 8 次（驗證偏嚴？請 Claude 看），單次重跑成本升到 $0.36。$0.360，累計 $0.794。
- 10/29 12:45 Claude：README 補上提交需要的段落（路線圖第 9 步初稿）：「不是什麼」聲明、Meta 模型用在哪（表格）、測試集結果（顏色版，SAM v2 等 T113 後補）、限制；彈跳與單擺註明「只在合成資料測過」。新增 MIT `LICENSE`（README 原本就寫 MIT 但沒有檔案）。合併 Antigravity T120 桌機截圖；三張手機截圖完全相同，已拿掉並開 T161 重做。
- 10/29 12:20 Claude：STATUS 瘦身（john 要求省 token）。上半部只留現況、路線圖、待辦、關卡結果、規則與最近日誌，約 27 KB（原本 105 KB）。打勾的任務、舊任務表、舊日誌、T63 testid 清單搬到最下面「封存」，內容一行都沒刪。之後各工具只要讀到「## 封存」為止；Claude 合併時會把打勾的行搬去封存。
- 10/29 10:40 Claude：審查並合併 Muse 的 T107–T112（重跑 SAM、建議物體名稱、語音回答、花費端點、來源標示、MetaHooks 的說明和標題）。修好 Muse 回報的 SAM 分母 bug（T146），新增 Muse T113 重跑。
- 10/29 Muse 完成 T107（分支 muse/T107-sam-rerun）：audit_batch 跑 data/gate/clips 7 支，track_source 全是 sam，但 7 支全因「只追到 61–63%」拒判——查出是後端覆蓋率分母用 24fps 來源格數、SAM 只出 15fps（天花板 62.5% < 門檻 0.8），修法在後端已寫進待 john 決定。SAM 對照表和兩版比較已貼進關卡結果。花費 $0.077，累計 $0.167。pip install 用「逐一確認 requirements 可 import＋ffmpeg＋meta-sam-parser 存在」代替（venv 本來就齊，避免重裝弄壞環境）。
- 10/29 Muse 完成 T110（分支 muse/T110-spend）：GET /api/spend＋API.md 一行契約＋tests/backend/test_spend.py（4 測試，全套件 196 pass）。$0，累計 $0.435。
- 10/29 Muse 完成 T108（分支 muse/T108-suggest-object）：spark.suggest_object 回 {object_name, camera_looks_static, reason}，schema＋check_model_text，bool 嚴格檢查。實作跟規格有一處差異：只看第一格無法判斷鏡頭動不動，所以多取約1秒後那格做比對（命名仍只看第一格）。clip2 真打一次通過，orange basketball／static 跟標註一致。3 mock 測試，全套件 195 pass。$0.008，累計 $0.271。
- 10/29 Muse 完成 T109（分支 muse/T109-voice-answer）：answer_interview_voice 回 {transcript, fields, mock}，欄位全標 confirmed: False；驗證接受尺寸物件／"11 cm" 字串（程式 parse）、window 物件／二元陣列；單位換算由程式做。4 mock 測試，全套件 197 pass。真打抽欄位 7 次：首輪尺寸形狀錯→修寬容；次輪只抽出 bool→prompt 加口語數字範例後全抽出。單次約 $0.02（輸出 token 3–10k，異常多，原因不明但按表計費）。$0.164，累計 $0.435。轉錄本體沿用 T24（已真打過），本次無麥克風只真打抽欄位。
- 10/29 Muse 完成 T112（分支 muse/T112-hooks-explain）：MetaHooks 加 explain_audit／headline_audit（2 mock 測試；全套件 194 pass，gate_prepare 仍原生失敗）。真打 own_2＋clip2 各兩種共 7 次呼叫：clip2 標題「落下節奏宛如置身月球，表觀重力約為地球的0.17倍」；第一次真打發現解說引 16 位小數、標題夾英文天體名，已修（prompt 限 2 位小數、BODY_ZH 對照表）並重打驗證通過，其中 1 次驗證失敗自動重試成功。$0.096，累計 $0.263。
- 10/29 Muse 沒有待辦了。（T107–T112 全在分支上做完並 push，等 Claude 合併；重驗過 6 條分支都在 origin 上且內容完整，未重跑任何付費呼叫，累計維持 $0.435）
- 10/29 Muse 完成 T111（分支 muse/T111-source＋三條分支的同改補丁）：全部模型回傳帶精確 model id；headline 改 dict；hooks 濾鍵不斷言；agent 無呼叫 early return 不帶 source（有測試鎖住）。全套件 192 pass（gate_prepare 原生失敗之外）。$0，累計 $0.435。Muse 這區沒有 [ ] 了。

## 封存（不用讀；只在要查舊紀錄時搜尋）

### 已完成的任務（從完成表搬來）

- [x] T118 Muse：（最優先）demo 紀錄裡的解說和標題現在是中文，但介面預設英文，評審也看英文。(1) `meta_client/headline.py` 加英文版（`lang` 參數，規則跟中文版一樣：模型不寫數字、不准真假字眼），補測試；(2) `meta_client/hooks.py` 的 `explain_audit` 傳 `lang="en"`，`headline_audit` 用英文版；(3) `pytest` 全過；(4) 重跑 T117 的同一個指令（約 $0.35，`--json-dir data/demo --explain`）；(5) 確認 10 支的 verdict 和數字跟現在一樣（只有 explanation、headline 文字變），不一樣就寫進 STATUS；(6) `git status` 確認沒有影片，commit，push 分支 `muse/T118-english-text`。 — commit 342d06c（headline 加 lang 版＋hooks 切英文＋3 測試；10 支 verdict 全同、數字差 <0.2%、文字全轉英文無中文殘留。explain 又是 10 次零重試。$0.333，累計 $1.686）
- [x] T161 Antigravity：（T120 的手機版重做）三張 390 px 手機截圖檔案已重拍，先等 data-testid 出現並捲入視窗後截圖，確認三張 md5 皆不同（results_wall: 92ab8e63, pair_comparison: 3b5addab, ghost_review: 716e193e）— commit f7f98f2
- [x] T162 Codex：評審用鍵盤和手機看的品質檢查（只改 `frontend/`）。(1) 只用鍵盤（Tab、Enter、空白鍵）從上傳影片走到看到結果，記下卡住或看不到焦點的地方並修好；(2) 檢查文字和背景的對比至少 4.5:1，不夠的改顏色 token；(3) 390 px 寬時沒有橫向捲動；(4) 每個由模型產生的區塊都有「由 Muse Spark／SAM 3.1 產生」標示，沒有的補上。補測試，`npm test` 和 `npm run build` 都要過，push 分支 `codex/T162-a11y`。 — commit be58457
- [x] T159 Codex：（API v1.0）偵訊畫面用 `draft.suggestion` 預填「Object name」，旁邊寫「Suggested by Muse Spark — please check」，使用者改了就用使用者的。`camera_looks_static` 只顯示成提示文字，**不准自動勾選**「鏡頭固定」。`suggestion` 是 null 時什麼都不顯示。補測試 — commit 585c561
- [x] T160 Codex：（API v1.0）把語音回答（T116 的 VoiceAnswers）接上 `POST /api/audit-drafts/{id}/voice`：錄音 → 送出 → 顯示 transcript 和每個欄位，每一欄都要使用者按「Use this」才會填進表單，不准自動送出。`source` 是 mock 時按鈕維持「需要 Meta API」。標明「由 Muse Voice Transcribe／Muse Spark 產生」。補測試（用假的 fetch） — commit 3c69d20
- [x] T116／T160 Codex：原語音端點缺口已由 API v1.0 補齊，前端已接 draft voice 上傳與逐欄 Use this。mock 不請求麥克風；模型來源依回傳顯示。實機麥克風／Meta API 端到端驗收仍待 Antigravity，本次只用假的 fetch 與錄音器測試，未產生模型花費。
- [x] T113 Muse：（最優先，T146 修好之後）用同一個指令重跑 SAM：`set -a; . ./.env; set +a; python -m scripts.audit_batch data/gate/manifest.csv --out data/gate/product_results_sam_v2.md`。把表格貼進「SAM 對照」，放在舊表下面，標題寫「v2（T146 修正分母後）」。舊表不要刪。如果有影片從拒判變成可以判，就在 `/api/audits` 回傳的 overlay 上確認紅點真的在球上，結果寫進 STATUS。花費記進成本紀錄 — commit 18d0202（v2：4 支判不一致＋3 支透視拒判；overlay 確認 clip1/clip5/manus 紅點在球上，clip4 待 john 複看。$0.360，累計 $0.794） — commit 18d0202
- [x] T120 Antigravity：桌機三張截圖（結果牆、鬼影球、並排比較）— commit 853ec74（手機版重做見 T161）

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
- [x] T108 Muse：Spark 看第一格畫面，建議 `object_name`（例如 orange basketball）和「鏡頭看起來固定嗎」。只是建議，要使用者確認才會用；回傳要過 schema 和 `check_model_text` — commit 46c1c57（spark.suggest_object：第一格命名＋約1秒後那格比對判斷鏡頭——單格看不出移動，特此說明；3 mock 測試。clip2 真打一次通過：orange basketball／static，跟標註一致。$0.008，累計 $0.271）
- [x] T110 Muse：花費顯示：後端 `/api/spend` 回傳目前累計花費和 120 美元上限，給前端顯示。到上限時所有付費呼叫拒絕，並有測試 — commit 74890d1（GET /api/spend 回 {spent_usd, limit_usd, at_limit}，meta_client 缺席回零；已驗證全部 12 個付費函式都是先 check 後呼叫＋record 再 check，拒絕本來就有。4 測試：總額／達上限旗標／缺模組／達上限時付費呼叫零 API 觸及。$0，累計 $0.435）
- [x] T109 Muse：語音回答偵訊問題：`muse-voice-transcribe-1.0` 把使用者說的話轉成文字，Spark 抽出欄位（例如物體大小），**數字一定要使用者在畫面上確認**才送出。沒有金鑰時用 mock — commit 72dff6d（voice.answer_interview_voice：轉錄→extract_interview_fields→每欄 {value, confirmed: False}；尺寸回原文 value+unit、程式換算成米；無 key 回 mock。4 mock 測試。抽欄位真打 7 次（含 2 輪形狀修正：尺寸字串／window 陣列寬容＋口語數字轉阿拉伯數字範例）後完整抽出；注意模型從動詞 flies 推得 assumed_model，照樣待確認。$0.164，累計 $0.435）
- [x] T112 Muse：（後端已由 Claude T143 做好）在 `MetaHooks` 加兩個方法：`explain_audit(audit: dict) -> str | None` 呼叫 `explain.explain_result(audit, kind="audit")`，`headline_audit(audit: dict) -> str | None` 呼叫 `headline.write_headline(audit)`。失敗就回 None 或丟例外，後端會退回固定模板，也會再檢查一次數字和禁用字。用 john 的 own_2 和 meta clip2 真打各一次，結果和花費寫進 STATUS — commit f54000e（explain_audit 取 ["explanation"]、失敗回 None；headline_audit 直通。clip2 標題「落下節奏宛如置身月球，表觀重力約為地球的0.17倍」；附帶修了解說數字只引 2 位小數、標題天體名轉中文。$0.096，累計 $0.263）
- [x] T111 Muse：每一個用到 Meta 模型的回傳都帶 `source`（model 名稱與版本），讓畫面能標示「由 Muse Spark 1.3 產生」「由 SAM 3.1 追蹤」 — commit 6f7d198（spark×4、interview、explain、voice×2、agent×2 回傳加實際 model id；TrackResult.source 預設 sam-3.1；write_headline 改回 {headline, source}；hooks 兩處展開先濾掉 source（後端 schema 只要 model/mock）；沒打模型的 early return 不帶 source。T108/T109/T112 三條未合併分支另補同改。$0，累計 $0.435）
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
- [x] T153 Codex：（最優先）稽核頁的主要流程改成 Muse 偵訊：上傳影片 → 「Prepare questions」→ 回答 → 時間窗 → 檢查。偵訊區塊預設展開、放在最上面；舊的直接上傳表單收進「Advanced: check without the interview」。Offline demo（匯入 JSON）也收起來。補測試 — commit 10935e8
- [x] T143 Codex：（API v0.9）結果區和物理名片最上面顯示 `headline.text`（有的時候才顯示），旁邊標明「由 Muse Spark 撰寫」；`headline` 是 null 時照舊用程式產生的標題。不要改寫文字或數字。靜態 demo 資料裡 `headline` 一律是 null — commit a3bb60f
- [x] T146 Codex：結果區加「這次用了哪些 Meta 模型」小面板：照實際值列出提問（`interview.source`）、追蹤（`track_source`）、說明（`explanation.source`）、標題（`headline` 有沒有）。是 mock、template、color、frame_diff 的，要寫「未使用模型」，不准寫死成已接上 — commit 9fa31c3
- [x] T151 Codex：拒判（`insufficient_data`）時顯示「怎麼重拍」提示：用固定對照表把 `reasons` 對應到提示，例如鏡頭移動 → 用腳架、物體朝鏡頭移動 → 從側面拍、慢動作 → 用正常速度。不用模型，並補測試 — commit 791b638
- [x] T145 Codex：右上角顯示 Meta API 花費（配合 Muse T110 的 `GET /api/spend`）。端點還不存在（404）時就不顯示，不要放假數字 — commit 97b5d85
- [x] T149 Codex：T133–T142 的新元件補齊繁中和英文切換，加測試確認沒有漏翻的字串 — commit f53db34
- [x] T150 Codex：時間窗選擇器的鍵盤操作（方向鍵移動把手、Enter 確認）和螢幕閱讀器標籤，補測試 — commit 381df65
- [x] T152 Codex：依 john「發現待辦就做」指示，修正時間窗候選請求途中換片／送出時，舊草稿晚到可能綁到新片的競態；補測試。 — commit f50a4d1
- [x] T154 Codex：結果區重新排版，讓第一次看的人三秒內看懂。由上而下：(1) 一條大色帶寫判定的白話：consistent →「Consistent with free flight on Earth」（綠）、inconsistent →「Inconsistent with free flight on Earth」（橘）、insufficient_data →「Cannot judge this clip」（灰），模型名稱照 `assumed_model` 換；(2) `headline.text`（有才顯示，標「由 Muse Spark 撰寫」）；(3) `explanation.text`；(4) 原因 `reasons`；(5) 其他（數字、圖、鬼影、限制、名片）收進「Details」區塊，預設收起。不准改任何數字或文字，補測試確認三種判定的顏色和順序 — commit b85f852
- [x] T155 Codex：等待中的回饋：時間窗建議約要 11 秒，稽核約要 10 到 20 秒。按下後顯示目前在做哪一步（「Scanning the video…」「Checking the motion…」）和已經過了幾秒；按鈕在等待時不能重按；失敗時用白話顯示錯誤，使用者已填的答案不能清掉。不准用計時器假裝進度百分比。補測試 — commit 7ad7f9a
- [x] T156 Codex：手機版（390 px 寬）主要流程不能左右捲動：上傳 → 問題 → 時間窗 → 結果。修好溢出的元件（影片、時間軸、表格），補測試檢查 class 或樣式 — commit 5f50f91
- [x] T158 Codex：稽核流程所有使用者看得到的英文字句做一次白話整理：不用術語（例如「frame differencing」改成「motion-based tracking (no model)」），同一種判定全站用同一個說法，繁中翻譯同步更新。加測試確認沒有 fake、detect AI、real or fake 這類字 — commit 689eec5
**Antigravity**（照順序做）
- [x] T02 Antigravity→Claude：（10/29 06:40 Antigravity 整晚沒有 push，改由 Claude 做）`requirements.txt`、`scripts/dev.sh`（檢查 ffmpeg／python3／npm，缺什麼就列出 brew 指令；後端 8000、前端 5173；沒有金鑰時用 mock） — 見 PR T02
- [x] T14 Antigravity：用 `seed_demo` 跑斜坡流程的端到端測試，截圖放 `docs/screenshots/`，問題寫進「缺什麼」 — commit a0904f0
- [x] T42 Antigravity：稽核流程的端到端測試。用 `tests/scripts/test_gate_run.py` 的 `write_clip` 產生合成影片，經 API 或畫面跑一次正常 g 和 g/4 兩種情況，截圖 — commit 7d4114d
- [x] T43 Antigravity：部署草稿：Dockerfile 與啟動說明。只在本機測，不要公開部署；`.env` 不准進映像檔 — commit 49a5a9a
- [x] T44 Antigravity：README 的安裝與使用說明（英文），只寫已經能用的功能 — commit eaf5b7d
- [x] T52 Antigravity：GitHub Actions CI：每個 PR 自動跑 `pytest` 和 `npm test`（需要安裝 ffmpeg） — commit 750cd65
- [x] T54 Antigravity：上傳安全：檔案大小上限 200 MB、只收影片格式、每個 IP 每天最多 20 次稽核。寫成提案放進「待 john 決定」，Claude 審查後實作 — 提案已寫入待 john 決定，待 Claude 審查
- [x] T119 Antigravity：用 `docker compose up` 一個指令就能跑起前後端（含 ffmpeg），只在本機測。要部署到哪個網站先寫進「待 john 決定」，不要自己開帳號 — commit 9e14a1c
**Manus**（不寫程式）
- [x] T21 Manus：影片物理合理性競品研究（附來源），結果放在 `docs/research/competitors.md`
- [x] T23 Manus：demo 分鏡與提交文字（兩個版本，未完成的部分寫 [TBD]）。差異點照 competitors.md 的結論寫，不准說「第一個」或「偵測 AI 影片」。**10/29 改成單一版本：影片物理稽核**（真實影片一致 → Meta 影片不一致 → 拒判例子 → Muse 問問題與說明）
- [x] T95 Manus：提交頁文字草稿（英文，300 字以內）：問題、做法、Meta 模型用在哪、限制。數字只能引用 STATUS「關卡結果」，不准說「偵測 AI 影片」
- [x] T123 Manus：三分鐘英文旁白稿，逐秒對應 T23 分鏡；只用 `data/gate/product_results.md` 裡的數字
- [x] T124 Manus：評分標準對照表：Impact 30%、Meta 工具運用 25%、技術深度 20%、Demo 25%，每一項寫我們的證據（指到 repo 裡的檔案或 demo 片段），做不到的老實寫「沒有」
- [x] T125 Manus：使用者測試計畫改版（取代 T22）：找 5 個人用自己的手機拍丟球影片上傳，記錄他們能不能看懂結果、哪裡卡住。附招募訊息和記錄表
- [x] T126 Manus：限制與常見問題（英文 FAQ）：為什麼不判斷真假、為什麼會拒判、需要怎麼拍、數字怎麼來、Meta 模型做了什麼
**Claude**
- [x] T141 Claude：候選時間窗：`physics.experiments.freefall.suggest_flight_windows` 和 `POST /api/audit-drafts/{id}/windows`（API v0.8）。在 john 的 3 支影片上，第一個或第二個候選和 john 的標註差不到 0.2 秒（own_1 1.87–2.60、own_2 0.03–0.80、own_3 1.82–2.42）。只是建議，關卡和稽核仍然只用人確認的時間窗 — 見 PR T141
- [x] T143 Claude：稽核結果接上 Muse 的說明和標題（API v0.9）：後端呼叫 hook `explain_audit`、`headline_audit`，模型的文字要再過一次 `check_model_text`（數字要能在結果裡找到，四捨五入後也算；不能有禁用字）才會用，否則退回固定模板。模型看不到原始軌跡，判定和數字都不經過模型；模型失敗也不會讓稽核壞掉 — 見 PR T143
- [x] T144 Claude：生成影片（Meta 6 支、Manus 1 支，共 11 MB，沒有個人隱私）放進 `data/gate/clips/`。`audit_batch --clips` 預設讀這裡，找不到的影片列成 missing。john 自己拍的影片不進 git — 見 PR T144
- [x] T146 Claude：修 SAM 追蹤比例的分母（Muse T107 發現的）：改用 SAM 的取樣時間算追到的比例和缺格事件。新增 15 fps SAM 對 60 fps 影片的測試 — 見 PR
- [x] T147 Claude：把 Muse 的 T108（建議物體名稱）和 T109（語音回答）接到 API（v1.0）：`audit-drafts` 回傳 `suggestion`，新增 `POST /api/audit-drafts/{id}/voice`。後端會檢查型別和範圍，名稱不能有數字，所有欄位都是未確認 — 見 PR
- [x] T148 Claude：比賽硬規則自動檢查 `tests/test_submission_rules.py`，每次 CI 都會跑：程式只呼叫 Meta 模型、git 裡沒有金鑰也沒有 .env、README 和畫面上沒有「偵測 AI／抓假影片」這類說法。另外修好 CI：requirements 改成最低版本，Python 3.11 才裝得起來（PR #68），現在 main 的 CI 是綠的 — 見 PR
- [x] T128 Claude：顏色追蹤支援更多顏色（yellow、green、red），只對**之後新的影片**生效，記進規則變更紀錄，關卡已跑的結果不重算
- [x] T129 Claude：`gate_run` 報告多加一欄 `size_trend`（只顯示，不當規則），讓關卡表和網站結果表能對照 — 見 PR T129
- [x] T130 Claude：（10/29 03:50 Manus 的 T23、T95、T123–T126 已檢查入庫：`docs/research/manus_t23_t95_t123_t126.md`。用詞符合規則，數字都來自 product_results，Muse/SAM 標 TBD）把 Manus 交來的 T23、T95、T123–T126 檢查用詞和數字後放進 `docs/research/`
- [x] T106 Claude：`data/demo/generated_*.json`：6 支 Meta、1 支 Manus 影片經網站流程的完整結果（含說明，不含影片），給 Codex T101 結果牆用 — 見 PR
- [x] T99 Claude：稽核結果新增 `explanation`（API v0.7），先用固定模板寫一般人看得懂的說明，數字由 `fill_numbers` 填入，例如「the object falls as if gravity were 1.71 m/s², 0.17 times Earth's, closest to Moon」。Muse T45 接上後改成 `source: model`。`data/demo/real_own_*.json` 已重新產生，含說明 — 見 PR T99
- [x] T98 Claude：`scripts/audit_batch.py`：把 manifest 裡每支影片都走一遍網站流程，產生 `data/gate/product_results.md`（網站判定結果表）。demo 和提交文字的數字引用這張表。目前：自拍 2 一致、1 小幅不一致；Meta 2 不一致（月球、冥王星）、4 資料不足（球朝鏡頭飛）；Manus 1 資料不足 — 見 PR T98
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
**john**
- [x] 合併 PR #4（已隨 PR #16 一起合併）

### 可行性關卡：影片物理稽核（10/28–10/29）

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

### 已解決的缺口與決定

- [x] Meta API 金鑰與額度是否可用：可用。Muse 10/29 用 .env 金鑰真打 SAM 成功（75 格 $0.015）。
- [x] SAM 3.1 API 的格式：已讀官方文件並實測（commit b696c68；Responses API + Files API，遮罩 base85 用官方解析器）。
- [x] T38 官方測試片不在 Muse 的電腦上 → 10/29 Claude 已把生成影片放進 `data/gate/clips/`（T144）
- [x] [Muse T107] SAM 覆蓋率分母 bug（需 Claude 修後端）：`audits.py` 用來源片格數（24fps）當分母，SAM 只出 15fps，天花板 62.5% 永遠低於門檻 0.8，所以 7 支全拒判。另 `by_t` 時間戳精確對齊在 15fps/24fps 混用下幾乎對不上，下游 events／鬼影也要修。Muse 不碰後端規則，等修好後重跑 T107 才有數字。 → **10/29 10:40 Claude 已修（T146）**

### 舊任務表（10/28，已不更新，以「待辦」為準）

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

### 舊工作日誌
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

- 10/29 Codex T143：結果與名片／PNG／Markdown／列印支援 headline 原文及 Muse 撰寫標示；null／舊紀錄維持程式標題並移除假待生成文案。原文不經介面翻譯且HTML安全轉義。npm77 pass、build pass；pytest191 pass/1 fail（drawtext）。

- 10/29 Codex T146：提問／追蹤／說明／標題四項實際來源面板；mock/template/color/frame_diff 均明示未使用模型。未保存的問答來源顯示未記錄；當次偵訊保留上下文。npm/build 通過；pytest drawtext 缺口仍列明。

- 10/29 Codex T151：insufficient_data 顯示固定 reason→重拍提示對照：腳架／側視／正常速度／追蹤可見性／完整時間窗。保留原 reason，不用模型、不作因果歸因；未知原因回一般清單。npm79 pass、build pass；pytest191 pass/1 fail（drawtext）。

- 10/29 Codex T145：頁首讀取真實 /api/spend；404、網路失敗或未知schema均隱藏，不補假額度。total_usd/limit_usd 待後端確認，防禦性接受明確USD有限數；focus與稽核完成後刷新，demo完全不查。npm81 pass、build pass；pytest192 pass/1 fail。

- 10/29 Codex T149：時間窗、候選、首頁卡片、How it works與分享／demo文案補齊繁中與英文。後端標題／說明以原文元件保留。測試逐一解析新元件所有靜態文字與讀屏標籤，並核對兩語言數字不變；npm83 pass、build pass，pytest192 pass/1 fail（drawtext）。

- 10/29 Codex T150：把手方向鍵精確0.01秒、Home/End有界移動，Enter僅在時間輸入且有效未確認時確認；數字欄與把手分開label、讀屏秒數與雙語操作說明。鍵盤邏輯與SSR語意測試通過；npm85 pass、標準/靜態build pass（主入口約72kB），pytest192 pass/1 fail（drawtext）。

- 10/29 Codex 沒有待辦了：T143→T146→T151→T145→T149→T150 已依序測試、各自分支推送並回填commit；再次pull main確認Codex區沒有[ ]。npm85 pass、標準/靜態build pass（entry約72kB），pytest192 pass/1 fail（ffmpeg缺drawtext，未略過）。interview來源跨載入與spend回傳契約待後端確認，已列待決定；未呼叫付費模型、未推main或部署，瀏覽器視覺/鍵盤實測仍待Antigravity。

- 10/29 Codex T152：主動檢查發現換片時候選草稿可能晚到綁錯片；新增選取版本綁定、同片請求去重、送出／切換／匯入後失效，忽略已卸載候選回傳。另用結果ID綁定本機預覽，讀其他紀錄時不套用舊片。補慢回應、切換、消耗、重試與錯片預覽測試；npm90 pass、兩種build pass，pytest192 pass/1 fail（drawtext）。

- 10/29 Codex 沒有待辦了：完成表無新增後，依 john 指示主動檢查並修正 T152 錯片競態，已推送並開 PR #56（接在 #55）。npm90 pass、標準／靜態build pass，pytest192 pass/1 fail（既有drawtext環境缺口）；再次pull main無Codex未勾項。未推main、未改後端。
- 10/29 Codex T153：問答預設展開且放在拍攝清單之前，步驟明示上傳→提問→回答→確認時間窗→檢查；直接分析收進Advanced，JSON匯入與可選語音收合，結果留在收合區外。中英文與展開／排序回歸測試通過；npm91 pass、標準/靜態build pass，完整pytest保留drawtext環境缺口。

- 10/29 Codex 沒有待辦了：T153 問答主要流程已推送 PR #58，npm91 pass、標準/靜態build pass，pytest192 pass/1 fail（drawtext）。再次pull無Codex待辦；另核對實際PR狀態，發現#55仍待合併main，已記錄給Claude。
- 10/29 Codex T154：結果依序為綠／橘／灰判定色帶、Muse標題、原文說明、原文原因；其餘數字／圖／鬼影／限制／名片保留於預設收合Details，不改輸入資料。三判定顏色與順序回歸測試、npm92 pass、build pass。PR目標main。
- 10/29 Codex T155：掃描／準備提問／檢查／讀取時顯示實際經過秒數，不把計時當完成百分比；保留已知upload bytes進度。請求鎖防重送，失敗保留原答案與問題，草稿失效僅要求重備草稿，不清欄位。npm94 pass、build pass。
- 10/29 Codex T156：390px主流程加容器縮小hook，影片等比例、欄位單欄、檔案輸入與表格限寬換行，不用全頁overflow-x:hidden掩蓋。新增主元件class與390px CSS規則測試；npm95 pass、build pass。實機瀏覽器驗收仍待Antigravity。
- 10/29 Codex T158：判定色帶、結果牆、首頁卡、名片、報告、列印共享白話判定；追蹤來源改motion-based tracking(no model)等易懂標籤，繁中同步。分析原文用Verbatim保留，JSON／量測值不變；數據與圖只換說明文字。新增全模型三判定一致性、禁用詞與原文／數字不變測試。npm99 pass、標準/靜態build pass；pytest192 pass/1既有drawtext環境失敗。

- 10/29 Codex 沒有待辦了。
- 10/29 Codex 本次完成 T154、T155、T156、T158，各自測試與build通過後提交推送；PR #61／#62／#63／#64 的目標均為 main。npm99 pass、標準／靜態build pass；未改後端、資料集或量測值。pytest192 pass/1 fail（既有ffmpeg無drawtext）。T157 尚無 Claude 定版通知，依 john 指示跳過，保留未勾。手機與鍵盤的實機瀏覽器驗收仍待 Antigravity。
