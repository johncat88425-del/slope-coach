# Submission text draft (T95 / T130)

Manus first draft (received 10/29 03:31) was written before the gate results existed, so it said "gate results not yet entered". Claude revised it with the numbers in `data/gate/product_results.md` and the STATUS gate results. Every number below comes from those two files.

---

**Slope Coach: does the motion in this clip match the physics you assume?**

Slope Coach checks a fixed-camera clip of a thrown, dropped, bouncing or swinging object against an explicit physics model. It tracks the object, fits the motion with deterministic code, and reports only "consistent", "inconsistent" or "insufficient data" with the assumed model, with the reasons, the raw numbers and the track overlay for human review. It does not judge whether a video is real or generated.

Meta models do the understanding: Muse Spark asks the user what it needs to know (object, time window, camera, size, slow motion) and explains the result in plain words, with every number filled in by the program; SAM 3.1 tracks the object. When SAM is not connected, a model-free colour + motion tracker is used and labelled as such.

Feasibility gate, one frozen rule set, labels by the author: two of the author's own throws gave apparent gravity of 9.62 and 9.81 m/s² (consistent); the website rated two of six Meta AI generated throws inconsistent (closest to the Moon and Pluto) and refused four because the ball moves towards the camera. Refusing is part of the product: when tracking, timing or scale is unreliable, it says so instead of guessing.

Limits: one camera, near side view, one object; the colour tracker was added after seeing the author's clips; one generator tested so far.
