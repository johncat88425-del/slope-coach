# Slope Coach: Video Physics Audit & Inquiry Coach

A neuro-symbolic physical inquiry and audit system developed for the **Meta Global AI Developer Hackathon (Indie Track)**.

Slope Coach audits moving objects in real-world or simulated videos against assumed physical motion models (such as free flight under constant gravity, bouncing balls, and single pendulums), and guides tabletop slope-and-slider mechanics experiments through an empirical "predict before you act" workflow.

All model calls in production are strictly restricted to Meta AI models (Meta SAM 3.1 and Meta Muse Spark). Every physical measurement and fit is computed deterministically by Python numerical routines—no language model ever invents or estimates raw measurement numbers.

**What it is not.** It does not judge whether a video is real or AI-generated, and it does not work on every video. A result only says whether the tracked motion is *consistent with*, *inconsistent with*, or *cannot be judged against* the motion model the user assumed. A real video can fail (bad framing, wrong scale), and a generated video can pass.

## Where Meta models are used

| Step | Meta model | What the model does | What it never does |
| --- | --- | --- | --- |
| Interview before the check | Muse Spark (`muse-spark-1.3`) | Looks at a few frames, suggests the object name, asks up to 3 questions (camera static? slow motion? object size?) | Fill in an answer for the user: every suggestion must be confirmed |
| Object tracking | SAM 3.1 (`sam-3.1`) | Segments the named object frame by frame | Produce physics numbers: the centroids go to `physics/` |
| Spoken answers | Voice Transcribe (`muse-voice-transcribe-1.0`) + Muse Spark | Turns a spoken answer into transcript and draft fields | Confirm a number: the user checks each field |
| Explanation and headline | Muse Spark | Writes a plain-language explanation of the result | Write any number: numbers are slot-filled by code, and the text is checked for causal or authenticity claims before it is shown (falls back to a template) |

Every model output is validated (JSON schema, value ranges, banned phrases) and labelled in the UI with the model that produced it. The backend refuses new paid calls once logged Meta API spend reaches US$120. Without `MODEL_API_KEY` the app runs with labelled mock hooks and colour tracking / frame differencing.

## Results on our test set (one frozen rule set, no per-clip tuning)

Main results use SAM 3.1 tracking (`data/gate/product_results_sam_v4.md`); colour tracking (`data/gate/product_results.md`) is shown for comparison. Rules were frozen in `scripts/gate_run.py` before any clip was run; later changes (all bug fixes, no threshold changes) are logged with old and new results in `docs/STATUS.md`.

| Clips | SAM 3.1 tracking | Colour tracking (comparison) |
| --- | --- | --- |
| 3 own clips of a thrown ball (phone, fixed camera) | 3 consistent (g = 9.30, 9.46, 8.68 m/s²) | 2 consistent (9.62, 9.81), 1 inconsistent (8.15) |
| 6 clips made with the Meta AI app | 3 inconsistent (g = 0.25, 0.14, 1.80 m/s²), 3 insufficient data (object size changes 34–48%) | 2 inconsistent, 4 insufficient data |
| 1 clip made with Manus | 1 inconsistent (g = 2.63 m/s²) | 1 insufficient data (tracked in 55% of frames) |

The two trackers do not always agree on which clips can be judged; both are reported. This is a small feasibility set, not a reliability benchmark. The own clips are not committed (privacy); the generated clips are in `data/gate/clips/`.

---

## Key Features (Currently Working)

### 1. Video Motion Physics Audit (`POST /api/audits`)
- **Model Verification**: Tests whether motion in an uploaded video clip is consistent with an assumed physical hypothesis (`free_flight`, `bounce`, or `pendulum`). Free flight is tested on real and generated clips; the bounce and pendulum checks are unit-tested on synthetic tracks but not yet on real clips.
- **Deterministic Trajectory Analysis**:
  - Automatically extracts object centroid coordinates across frames (using frame differencing / color tracking, with zero-shot segmentation hooks for Meta SAM 3.1).
  - Fits apparent gravitational acceleration ($g_{\text{apparent}}$) and initial velocities ($v_{x0}, v_{y0}$) via least-squares optimization.
  - Compares the observed acceleration to reference celestial bodies (Earth: $9.81\text{ m/s}^2$, Moon: $1.62\text{ m/s}^2$, Mars: $3.71\text{ m/s}^2$, etc.).
  - Computes the implied time factor, which flags footage that may be slowed down.
- **Ghost Trajectory Comparison**:
  - Projects theoretical "ghost" coordinates following standard Earth gravity ($9.81\text{ m/s}^2$) directly alongside real empirical points.
- **Principled Abstention**:
  - Explicitly refuses to guess when filming prerequisites fail (e.g. non-static handheld camera, severe target occlusion, or ambiguous release frames).
  - Verdicts are strictly model-relative: `consistent`, `inconsistent`, or `insufficient_data`.

### 2. Slope & Slider Inquiry Coach (`POST /api/experiments`)
- **Scene Calibration**: Marks ruler pixel scale, slope length $L$, and vertical height $h$ from user confirmation.
- **Predict-Before-Act Locking**: Freezes theoretical quadratic prediction equations ($s(t) = s_0 + v_0 t + \frac{1}{2} a t^2$) with an immutable timestamp prior to trial ingestion.
- **Controlled Intervention Recommendations**: When discrepancy exceeds tolerance, recommends falsifiable follow-up tests (`release_check` via barrier release vs `dimension_check` via height re-measurement).

### 3. Interactive Web UI (`frontend/`)
- Modern single-page web app built with React, Vite, and TypeScript.
- **Audit Page & Guided Demo**: Upload video or replay pre-computed offline demonstrations (`synthetic_consistent`, `synthetic_inconsistent`, `synthetic_insufficient`, and real benchmark clips).
- **Trajectory Visualizer & Charts**: High-contrast, accessible 2D plots (cyan dashed lines for predictions, orange solid lines for observations).
- **Physics Card Export**: Generates and downloads a summary badge with overlay snapshots, empirical numbers, and boundaries.
- **Bilingual Interface**: Full support for English and Traditional Chinese.

---

## System Requirements

- **Operating System**: macOS or Linux (Ubuntu 22.04+ recommended)
- **Python**: 3.11+
- **Node.js**: 20+ (with npm)
- **ffmpeg & ffprobe**: Required for video decoding and overlay rendering
- **Meta Model API Key**: Optional for local synthetic testing, required for live Meta AI inference

---

## Installation & Setup

### 1. Clone Repository
```bash
git clone https://github.com/johncat88425-del/slope-coach.git
cd slope-coach
```

### 2. Install System Dependencies

**macOS (via Homebrew)**:
```bash
brew install ffmpeg python@3.11 node@20
```

**Ubuntu / Debian**:
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3-pip python3-venv nodejs npm
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env to add your MODEL_API_KEY if testing live Meta models
```

### 4. Install Python Backend Dependencies
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Install Frontend Dependencies
```bash
cd frontend
npm ci
cd ..
```

---

## Running the Application

### Option A: One-Command Development Script
```bash
./scripts/dev.sh
```
This concurrently starts:
- FastAPI Backend: `http://localhost:8000` (API documentation at `/docs`)
- Vite Frontend: `http://localhost:5173`

Press `Ctrl+C` to terminate both services cleanly.

### Option B: Manual Execution
**Terminal 1 (Backend)**:
```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend)**:
```bash
cd frontend
npm run dev -- --port 5173
```

---

## Running Tests

### Backend & Physics Unit Tests
```bash
source .venv/bin/activate
pytest -v
```

### Frontend Unit & Verification Tests
```bash
cd frontend
npm test
```

### End-to-End Verification Scripts
```bash
source .venv/bin/activate

# 1. Slope Coach E2E synthetic demo
python scripts/e2e_slope_demo.py

# 2. Video Audit E2E test with ffmpeg clip synthesis
python scripts/e2e_audit.py
```

---

## Limitations

- One object, fixed camera, roughly side-on view. Handheld footage, objects moving toward the camera (size change over 30%), slow motion, and gaps in tracking are refused rather than guessed.
- 2D only: no depth, no live streaming.
- The metre scale comes from a user-entered object size; a wrong size scales g by the same factor.
- Generated clips were made with consumer apps at one point in time; results say nothing about other generators or later versions.

---

## Project Structure

```
slope-coach/
├── backend/          # FastAPI routes, schemas, state store, and audit logic
├── physics/          # Pure deterministic physics functions (freefall, slope, fit)
├── frontend/         # React + TypeScript single-page application
├── scripts/          # Developer tooling, dev.sh, seed_demo, and e2e runners
├── docs/             # Technical specifications, audit reports, screenshots
├── tests/            # Automated test suites (backend, physics, frontend, e2e)
├── requirements.txt  # Python package dependencies
├── Dockerfile        # Container build draft
└── README.md         # Project documentation
```

---

## License & Attribution
Developed for the Meta Global AI Developer Hackathon. Open-source under the MIT License (see `LICENSE`). All work was done during the hackathon period (from 2026-10-26).
