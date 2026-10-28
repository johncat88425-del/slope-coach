# Slope Coach frontend — T08 / T09

React + Vite + TypeScript website for users' real experiment photos and videos.
No simulation, generated experiment footage, 3D, or runtime model calls.

```sh
npm ci
npm test
npm run build
npm run dev
```

Use Node 20 or newer. The test command compiles the shared TypeScript module before
running Node's built-in test runner. Vite prints the local URL.

Five hash routes: `#setup`, `#prediction`, `#analysis`, `#verification`, `#report`.
All views read the same typed in-memory experiment record. Navigation and browser
Back/Forward preserve that record. Refresh clears it; files are never sent to a server.

1. Choose a real experiment photo. Click the ruler's two ends, then the slider.
   Coordinate fields provide a keyboard alternative; Undo removes the last point.
2. Enter measured slope length L, vertical height h, and ruler segment distance in
   metres. Confirm the capture conditions. Save the calibration draft.
3. Missing/unreadable photos, missing/out-of-bounds markers, coincident ruler
   endpoints, nonpositive/nonfinite dimensions and h ≥ L block saving.
4. Visit Prediction or Report to see the same confirmed values. Editing setup
   invalidates the saved draft. Replacing a photo clears markers and confirmation.
5. In Analysis, choose your own video for local playback. This is a preview, not
   submission: prediction locking and analysis remain unavailable until T07.

Prediction uses a cyan dashed line legend; observed data uses an orange solid
line legend, both with text labels. No physical data or charts are fabricated.
Backend analysis, immutable prediction records, interventions and report exports
are pending. Proposed endpoints are recorded in docs/STATUS.md, not an API contract.

`npm test` covers validation, responsive pixel mapping, routing, immutable saved
snapshots and stale-calibration invalidation. Build checks TypeScript and bundling.
