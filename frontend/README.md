# Slope Coach frontend

React + Vite + TypeScript client for the real FastAPI API described in
`../docs/API.md` and `../backend/schemas.py`.

```sh
npm ci
npm test
npm run build
npm run dev
```

Use Node 20+. Start the backend separately at **http://localhost:8000**.
Vite proxies `/api` to that address, so either `127.0.0.1:5173` or
`localhost:5173` works without changing backend CORS. For a deployed frontend,
configure its reverse proxy the same way, or set `VITE_API_BASE_URL` to an API
origin with appropriate backend CORS. This frontend does not change the API.

## Workflow

- Create an experiment, or enter its ID to resume. The last ID is stored in
  browser localStorage; refresh only performs GET, never repeats mutations.
- Upload your photo to scene-photo. The UI displays model/mock source and
  retake reasons. Mock scene checks are not treated as verified measurements.
- Mark ruler endpoints, slider as path start, then the path end in original image pixels.
  Path endpoints are required by API v0.1. Enter measured ruler distance, L and
  h in metres and confirm capture conditions. Save an append-only calibration.
  The API stores ruler/path geometry, but has no slider-marker field; that
  single marker remains local. No physical conversions run in the frontend.
- Upload at least three baseline videos under Analysis. Run tracking, confirm
  release time, and select those trials under Prediction to create a baseline.
- If tracking returns 501, manually mark the slider in paused video frames.
  Turn manual mode off to seek using video controls, then turn it back on.
  Missing frames can be marked explicitly. Saving replaces the trial's full
  detection list; samples retain `manual` source. Nothing is interpolated.
- Select calibration/baseline versions, enter a measured distance, and create
  a locked prediction. Only then can a test or intervention video be submitted.
  Changing the selected prediction/calibration clears the pending test upload
  and requires reconfirming release assumptions.
- Compare the locked prediction and selected test trial. Insufficient data is
  displayed as a normal outcome, with failed checks and can_still_say.
- Choose only checks returned in comparison evidence. Read both finding and
  cannot_distinguish, follow the backend instructions, create a new prediction
  before repeating, then link the intervention trial.
- Download Markdown and CSV directly from the backend report endpoints.

Prediction is cyan/dashed, observations orange/solid. Observations with any
non-ok quality create line breaks. The comparison chart uses media time minus
confirmed t0 and subtracts backend fit.s0_m for display in prediction coordinates;
no fitting, parameter estimation, best-fit time alignment or video overlays run
in the frontend.

## Known backend dependencies

The default backend still uses MockHooks: scene/release suggestions are labelled
mock, and SAM returns 501. T26 now persists backend records to its configured store file. Backend T30 now serves `/media/...` and supplies photo URLs. This frontend still
uses selected local files for preview until T36 adds the media proxy and rendering.
After refresh, reselect the original clip without uploading again. T36 starts
after john merges PR #4, as required by docs/STATUS.md. Real Meta hooks and
physical accuracy with independent real clips remain separate work.

Requests have a 120-second timeout, preserve HTTP errors, and never automatically
retry mutations. On a timeout or partial failure, refresh the experiment first
before deciding whether to submit again. No API key belongs in the frontend.

Tests cover calibration validation/pixel mapping/version invalidation and API
payloads, multipart boundaries, normal insufficient-data responses, errors and
text report downloads. They do not claim real-video accuracy or model readiness.
