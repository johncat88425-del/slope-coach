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

## 欄位說明

- 上傳的檔案由後端放在 `/media/{eid}/{檔名}`：`TrialOut.video_url` 和 `scene-photo` 回傳的 `photo_url` 都是這個路徑。開發時 Vite 要把 `/media` 也代理到後端。
- `TrialOut.samples[]`：`{t_s, s_m 或 null, quality, source}`。`quality` 有五種：`ok`、`missing`、`area_jump`、`position_jump`、`off_path`。只有 `ok` 能畫成實測點；其他要畫成缺口，**不能連線**。
- `PredictionOut.curve[]`：`[t, s]`，t 從起滑開始算，s 從釋放位置開始算。疊到影片上時，播放時間要先減掉 `t0_s`，s 要加上釋放位置（`ComparisonOut.fit.s0_m`）。預測到達終點後就停止，不要再畫。
- `PredictionOut.overlay_px[]`：`[t, x_px, y_px]`，假設釋放位置就在路徑起點換算成像素。實際釋放位置不在起點時，要沿路徑方向平移 `fit.s0_m / m_per_px` 個像素。只有校準和起滑時刻都確認後才顯示疊加。
- `ComparisonOut.checks[]`：`{name, passed, detail, blocking}`。有任何 `blocking: true` 的項目沒通過，結果就是 `insufficient_data`。
- `ComparisonOut.evidence[]`：下一次驗證的候選，由 physics 依數字產生，目前只有 `dimension_check` 和 `release_check` 兩種。每個候選附 `finding`（數字顯示什麼）和 `cannot_distinguish`（目前還分不出什麼），兩者都要顯示給使用者。

## Meta 模型接入點（給 Muse Code）

`backend/model_hooks.py` 定義了 `ModelHooks` 介面，共三個方法：`check_scene`、`track_slider`、`suggest_release_time`。預設的 `MockHooks` 不連網路。`meta_client` 寫好後，在啟動時呼叫 `set_hooks(MetaHooks())` 替換掉它。選下一次驗證的代理（T11）只能從 `ComparisonOut.evidence` 的候選中挑一個，並把理由放進 `model_rationale`。
