# API 契約（前後端）v0.1

後端：`uvicorn backend.main:app --reload`（預設 http://localhost:8000），互動文件在 `/docs`。所有欄位名稱以 `backend/schemas.py` 為準；要改契約，先在 `docs/STATUS.md` 的「待 john 決定」提出。

沒有真影片時，可以先執行 `python -m scripts.seed_demo --case pushed` 建立示範實驗（合成資料，標為 manual）。

單位：時間用秒（`_s`），距離用米（`_m`），像素用 `_px`。`s` 是沿斜坡路徑、從使用者確認的路徑起點量起的距離。

## 資料原則（前端也要遵守）

- **數字只來自後端的 physics 計算。** 前端只負責顯示，不自己算物理。
- **預測一旦建立就鎖定**，沒有修改端點，送 PUT/PATCH/DELETE 會得到 405。要改尺寸，就建新的 calibration 版本，再建新的 prediction。
- **預測必須在試驗影片上傳之前建立**，否則比較會回傳 409。
- 模型寫給使用者的文字會經過 `backend/output_check.py`：數字必須出自工具輸出，禁止「證實」「真因」等因果誇大用語，不通過回 422。
- 每個數字都標明來源：`source: "user" | "model" | "mock" | "sam" | "manual"`。畫面要讓人分得出哪些是使用者確認的、哪些是影像估計的。
- `verdict: "insufficient_data"` 是正常結果，不是錯誤。畫面要顯示 `checks` 裡沒通過的項目，以及 `can_still_say` 的內容。

## 流程與端點

| 步驟 | 方法與路徑 | 送出 | 回傳 |
| --- | --- | --- | --- |
| 建立實驗 | `POST /api/experiments` | `{title?}` | `ExperimentOut` |
| 讀整個實驗紀錄 | `GET /api/experiments/{eid}` | | `ExperimentOut`（所有子紀錄） |
| 場景照片檢查 | `POST /api/experiments/{eid}/scene-photo` | multipart `file` | `{photo_id, photo_url, scene_check}`；`needs_retake: true` 時要求重拍並顯示 `retake_reasons` |
| 校準與尺寸 | `POST /api/experiments/{eid}/calibrations` | `{ruler_px:[[x,y],[x,y]], ruler_length_m, path_start_px:[x,y], path_end_px:[x,y], slope_length_m, slope_height_m, reason?}` | `CalibrationOut`（含 `version`、`m_per_px`、`angle_deg`）；0 < h < L 不成立時回 422 並附原因 |
| 上傳試驗 | `POST /api/experiments/{eid}/trials` | multipart：`kind`（`baseline` / `test` / `intervention`）、`calibration_version`、`file`（影片，選填） | `TrialOut` |
| 自動追蹤 | `POST /api/trials/{tid}/track?text_prompt=...` | | `TrialOut`；SAM 還沒接上時回 501，畫面要改成提供手動點選 |
| 手動或外部偵測 | `PUT /api/trials/{tid}/detections` | `{detections:[{t_s, centroid_px:[x,y] 或 null, area_px?, source:"sam" 或 "manual"}]}` | `TrialOut`（每格附 `quality`） |
| 起滑時刻建議 | `GET /api/trials/{tid}/release-suggestion` | | `{source, candidate_t0_s, reason}`，只是建議 |
| 確認起滑時刻 | `PUT /api/trials/{tid}/release-time` | `{t0_s}` | `TrialOut`（`t0_source: "user"`） |
| 基準校準 | `POST /api/experiments/{eid}/baselines` | `{trial_ids:[3 個以上 baseline], calibration_version}` | `BaselineOut`（`mu_eff ± mu_spread`），每次建立都是新版本 |
| 鎖定預測 | `POST /api/experiments/{eid}/predictions` | `{calibration_version, baseline_version, distance_m}` | `PredictionOut`（`curve`、`overlay_px`、`assumptions`、`created_at`） |
| 比較 | `POST /api/experiments/{eid}/comparisons` | `{prediction_id, trial_id}` | `ComparisonOut`（`verdict`、`checks`、`fit`、到達時間誤差、`residuals`、`evidence`） |
| 選下一次驗證 | `POST /api/experiments/{eid}/interventions` | `{comparison_id, check_type, model_rationale?}` | `InterventionOut`（含固定的操作說明）；`check_type` 不在 `evidence` 候選內時回 422 |
| 連結驗證結果 | `PATCH /api/interventions/{iid}` | `{result_trial_id}` | `InterventionOut` |
| 報告 | `GET /api/experiments/{eid}/report.md`、`report.csv` | | 文字檔 |
| 花費顯示 | `GET /api/spend` | | `{spent_usd, limit_usd, at_limit}`（T110；累計花費、上限 120 美元、是否已達上限；達上限時所有付費呼叫拒絕） |

## 影片物理稽核（T37，v0.2 新增）

| 步驟 | 方法與路徑 | 送出 | 回傳 |
| --- | --- | --- | --- |
| 建立稽核 | `POST /api/audits` | multipart：`file`（影片）、`t_start`、`t_end`（秒，由使用者確認）、`camera_static`（true/false）、`assumed_model`（`free_flight`、`bounce`、`pendulum` 或 `vehicle`）、`object_size_m`（選填，使用者提供；`vehicle` 時是車身長度） | `AuditOut` |
| 讀取稽核 | `GET /api/audits/{aid}` | | `AuditOut` |

`AuditOut` 的欄位：
- `verdict`：只會是 `consistent`、`inconsistent` 或 `insufficient_data`，**都是相對於 `assumed_model`**。畫面上不准寫成「真影片」或「AI 影片」。
- `reasons[]`：判定的原因，或拒判的原因。
- `numbers{}`：程式算出的數字。可能有 `g_apparent_m_s2`、`implied_time_factor`、`implied_object_size_m`、`tilt_deg`、`rms_over_travel`、`tracked_fraction`、`n_points`。沒算出來的就不會出現。自由飛行另有「重力當尺」四個數（不需要尺寸，**假設**是地球重力、正常速度、正側面）：`if_earth_flight_time_s`、`if_earth_vertical_extent_m`（軌跡最高到最低的垂直距離）、`if_earth_launch_speed_m_s`、`if_earth_launch_angle_deg`（第一個追蹤點相對水平的角度，負的是往下）。這是在假設下的讀數，不是判定；慢動作 2 倍會讓高度讀成 4 倍。
- `points[]`：`[t, x_px, y_px]`，座標以寬 480 px 的畫面為準。
- `assumed_model=pendulum`（v0.3）：單擺。可另外送 `length_m`（使用者自己量的擺長，公尺）。`numbers` 會有 `period_s`、`period_spread`（各次擺動週期的差異比例）、`implied_length_m`（由週期推算的擺長），有給 `length_m` 時還有 `predicted_period_s`。週期只用水平位置算，不需要尺寸。
- `assumed_model=vehicle`（v1.1，T175）：車子從側面開過、鏡頭固定。`object_size_m` 是**使用者確認的車身長度**（公尺；一般轎車約 4.5）。車身在畫面上的像素長度由追蹤框寬度算（取和中位數差 10% 以內的影格，車頭被畫面切到的影格不算）。判定：需要超過 1.2 g 的加速或煞車、或軌跡跳動不平順 → `inconsistent`；沒給車長時用 3 m 和 6 m 兩種車長都算，兩個答案一樣才判，不一樣回 `insufficient_data`。慢動作、鏡頭在動、車子變大變小超過 30%（往鏡頭開）、車子移動不到一個車身長 → `insufficient_data`。`numbers` 會有 `car_length_px`、`speed_car_lengths_s`（每秒幾個車身，不需要公尺）、`accel_car_lengths_s2`、`car_length_for_max_accel_m`（車要多長，這個加速度才剛好是 1.2 g）、`n_points`，有車長時還有 `speed_m_s`、`speed_km_h`、`accel_m_s2`（負的是減速）、`accel_g`（絕對值）。沒給車長時還有 `car_length_low_m`、`car_length_high_m`（試的車長範圍）和對應的 `speed_km_h_low/high`、`accel_g_low/high`。選填 `vehicle_class`（v1.2，T190）：`compact_car`（4.3–4.75 m）、`sedan`（4.6–5.0 m）、`suv`（4.5–4.85 m）、`pickup`（5.3–5.95 m）或 `unknown`（3–6 m），由使用者確認；有 `object_size_m` 時以 `object_size_m` 為準。範圍來源見 `docs/research/vehicle.md`。
- `DetectionIn.width_px`（v1.1，T175，選填）：追蹤框寬度。稽核用的 SAM 回傳跟 `centroid_px` 一樣是**畫面寬度的比例**（0 到 1）。只有 `vehicle` 會用到。
- `track_check`（v1.3，T207）：Muse Spark 複查 SAM 追蹤。`{same_object: true/false, note, source: "model"}`；`note` 是一句話、沒有數字（有數字就清成空字串）。只有 `track_source=sam` 且追蹤夠完整時才會跑；沒接模型或失敗是 `null`，畫面就不顯示。`same_object=false` 只是警告（11/01 改）：判定和數字照程式算的不變，畫面在結果旁邊顯示「⚠ Muse Spark 複查：可能追錯物體，請看軌跡圖」。原因：同一支影片兩次跑，Spark 一次說 true、一次說 false，模型的回答不能推翻固定規則算出的判定。
- `retake_tips`（v1.3，T207）：判定是 `insufficient_data` 時 Muse Spark 寫的 1 到 3 條重拍建議（字串陣列）；每條都要通過後端檢查（沒有結果以外的數字、沒有禁用字眼），有一條不過就整個是 `null`，畫面退回固定建議。
- `what_would_fit`（v1.3，T207）：自由飛行判定是 `inconsistent` 時 Muse Spark 寫的「要怎樣才會一致」一句話，格式和 `headline` 一樣 `{source: "model", text}`；數字只能是結果裡已有的（例如 `implied_time_factor`）。沒有就是 `null`。
- `ghost_points[]`（v0.3）：「鬼影軌跡」。物體從同一點、用同樣的初速度出發，但以 9.81 m/s² 往畫面正下方落下時，每個時間點應該在的位置。只有填了 `object_size_m` 才會有。前端畫成虛線，和實測點並排。
- `nearest_body`（v0.3）：表觀重力最接近的星球（Pluto、Moon、Mars、Earth、Jupiter），搭配 `numbers.g_vs_earth`（表觀 g 是地球的幾倍）。只是幫助理解的比喻，不是判定。
- `numbers.g_apparent_low`、`g_apparent_high`、`g_verdict_robust`（v0.3）：物體像素大小估錯 ±30% 時，表觀 g 的範圍。`g_verdict_robust` 為 1 表示判定在這個範圍內都不變，0 表示判定會因尺寸誤差翻轉，畫面要提醒使用者。
- `overlay_url`：軌跡疊加圖，給使用者確認追蹤點有落在物體上。
- `events[]`：物體持續性事件（消失、大小跳動、位置跳動），附發生時間。
- `POST /api/audit-drafts/{draft_id}/windows`（v0.8，表單 `object_name`）：程式（不是模型）掃影片前 15 秒，回傳候選飛行時間窗 `windows: [{t_start, t_end}]`，依時間排序，`source: "physics"`。只是建議，使用者要自己選一個並確認，稽核只用使用者確認的時間窗。
- `AuditOut.headline`（v0.9，T143）：`{source: "model", text}` 或 `null`。這是 Muse Spark 寫的一句標題，數字由程式填入，並通過後端檢查。沒接上模型、模型失敗或沒通過檢查時是 `null`。`explanation.source` 有 Muse 接上時會是 `model`，同樣要先通過後端檢查，否則是 `template`。判定和數字都不經過模型。
- `AuditDraftOut.suggestion`（v1.0，T147）：`{source, object_name, camera_looks_static, reason}` 或 `null`。這是 Muse Spark 看前幾格畫面猜的物體名稱，**只能拿來預填，使用者要確認或修改**。名稱裡有數字、或沒通過禁用字檢查時是 `null`。
- `POST /api/audit-drafts/{draft_id}/voice`（v1.0，T147，multipart：`audio`，10 MB 以內）→ `{source: {transcript, fields}, transcript, fields}`。`fields` 只會有 `camera_static`、`slow_motion`（布林）、`object_size_m`、`length_m`（公尺，0 到 100）、`assumed_model`、`time_window`（`[開始, 結束]`），每一欄都是 `{value, confirmed: false}`。後端不會套用任何欄位，畫面要讓使用者逐欄確認後，再當成一般答案送 `POST /api/audits`。沒接上模型時回 `source: mock`、`fields: {}`；模型失敗回 502。
- `explanation`（v0.7）：`{source, text}`，用一般人看得懂的話說明結果。`source` 是 `template`（固定模板，未使用模型）或 `model`（Muse Spark 寫的，T45）。不論哪一種，文字裡的數字都由程式用 `fill_numbers` 填入，也通過禁用語檢查。畫面要標明來源。
- `track_source`：`sam`（畫面要標明「由 SAM 3.1 追蹤」）、`color`（v0.6：沒接 SAM、而且 `object_name` 含顏色時，例如 `orange ball`，用顏色＋移動追蹤，未使用模型）、`frame_diff`（其他情況）、`manual`。
- `limits[]`：已知限制，畫面要顯示。
- 物體大小沿軌跡變化超過 30%（`numbers.size_trend`），表示物體朝鏡頭或遠離鏡頭移動，結果會是 `insufficient_data`。
- `bounce` 模式會回傳 `rebound_ratio_k`，代表第 k 次反彈高度除以前一次高度。大於 1 加上容差就判不一致。

## 欄位說明

- 上傳的檔案由後端放在 `/media/{eid}/{檔名}`：`TrialOut.video_url` 和 `scene-photo` 回傳的 `photo_url` 都是這個路徑。開發時 Vite 要把 `/media` 也代理到後端。
- `TrialOut.samples[]`：`{t_s, s_m 或 null, quality, source}`。`quality` 有五種：`ok`、`missing`、`area_jump`、`position_jump`、`off_path`。只有 `ok` 能畫成實測點；其他要畫成缺口，**不能連線**。
- `PredictionOut.curve[]`：`[t, s]`，t 從起滑開始算，s 從釋放位置開始算。疊到影片上時，播放時間要先減掉 `t0_s`，s 要加上釋放位置（`ComparisonOut.fit.s0_m`）。預測到達終點後就停止，不要再畫。
- `PredictionOut.overlay_px[]`：`[t, x_px, y_px]`，假設釋放位置就在路徑起點換算成像素。實際釋放位置不在起點時，要沿路徑方向平移 `fit.s0_m / m_per_px` 個像素。只有校準和起滑時刻都確認後才顯示疊加。
- `ComparisonOut.checks[]`：`{name, passed, detail, blocking}`。有任何 `blocking: true` 的項目沒通過，結果就是 `insufficient_data`。
- `ComparisonOut.evidence[]`：下一次驗證的候選，由 physics 依數字產生，目前只有 `dimension_check` 和 `release_check` 兩種。每個候選附 `finding`（數字顯示什麼）和 `cannot_distinguish`（目前還分不出什麼），兩者都要顯示給使用者。

## Meta 模型接入點（給 Muse Code）

`backend/model_hooks.py` 定義了 `ModelHooks` 介面，共五個方法：`check_scene`、`track_slider`、`suggest_release_time`、`interview_audit`（v0.4）、`track_object`（v0.5，給稽核用的 SAM 3.1 追蹤：座標要正規化到 0..1，面積是佔整個畫面的比例，每一格一筆，找不到物體時 centroid 為 null；沒接上時丟出 `TrackingUnavailable`，後端會改用 frame differencing）。`POST /api/audits` 新增 `object_name`（給 SAM 的文字提示，預設 "ball"），結果裡的 `track_source` 會標明是 `sam` 還是 `frame_diff`。預設的 `MockHooks` 不連網路。`meta_client` 寫好後，在啟動時呼叫 `set_hooks(MetaHooks())` 替換掉它。選下一次驗證的代理（T11）只能從 `ComparisonOut.evidence` 的候選中挑一個，並把理由放進 `model_rationale`。

### Muse 偵訊（v0.4，T78）

兩個步驟，舊的單一步驟 `POST /api/audits`（直接送 file）仍然可用。

1. `POST /api/audit-drafts`（multipart：`file`）→ `201 {draft_id, video_url, interview}`
    - `interview.source`：`model`（由 Muse Spark 提問）或 `mock`（固定問題）。模型沒接上、失敗，或問題沒通過檢查時，都會是 `mock`，原因寫在 `interview.note`。
    - `interview.questions[]`：最多 3 題，每題是 `{field, text}`。`field` 是 `camera_static`、`slow_motion`、`object_size_m`、`time_window`、`assumed_model` 或 `length_m`，代表這題的答案要填到哪個欄位。`text` 不准含數字（10 以下的整數除外），也不准有真偽、因果字眼。
2. 使用者回答後，呼叫 `POST /api/audits`，用 `draft_id` 取代 `file`，再加上使用者確認過的欄位。新欄位 `slow_motion`（布林）：使用者說是慢動作時，`free_flight` 和 `pendulum` 會回 `insufficient_data`，因為時間不是真實時間。
    - 一個 `draft_id` 只能用一次，再用會回 404。`file` 和 `draft_id` 必須剛好送一個，否則回 422。
- 前端顯示問題時要標明「由 Muse Spark 提問」（`source=model`）或「固定問題」（`source=mock`）。
- 模型只負責提問，答案（數字、是否固定、是否慢動作）一律由使用者輸入。

