# Slope Coach: Video Physics Audit & Inquiry Coach

A neuro-symbolic physical inquiry and audit system developed for the **Meta Global AI Developer Hackathon (Indie Track)**.

Slope Coach audits moving objects in real-world or simulated videos against assumed physical motion models (such as free flight under constant gravity, bouncing balls, and single pendulums), and guides tabletop slope-and-slider mechanics experiments through an empirical "predict before you act" workflow.

All model calls in production are strictly restricted to Meta AI models (Meta SAM 3.1 and Meta Muse Spark). Every physical measurement and fit is computed deterministically by Python numerical routines—no language model ever invents or estimates raw measurement numbers.

---

## Key Features (Currently Working)

### 1. Video Motion Physics Audit (`POST /api/audits`)
- **Model Verification**: Tests whether motion in an uploaded video clip is consistent with an assumed physical hypothesis (`free_flight`, `bounce`, or `pendulum`).
- **Deterministic Trajectory Analysis**:
  - Automatically extracts object centroid coordinates across frames (using frame differencing / color tracking, with zero-shot segmentation hooks for Meta SAM 3.1).
  - Fits apparent gravitational acceleration ($g_{\text{apparent}}$) and initial velocities ($v_{x0}, v_{y0}$) via least-squares optimization.
  - Compares the observed acceleration to reference celestial bodies (Earth: $9.81\text{ m/s}^2$, Moon: $1.62\text{ m/s}^2$, Mars: $3.71\text{ m/s}^2$, etc.).
  - Computes implied time factor (detecting unintentional slow-motion effects).
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
Developed for the Meta Global AI Developer Hackathon. Open-source under the MIT License.
