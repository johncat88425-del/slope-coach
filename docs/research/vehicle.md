# T178 — Slope Coach: Reference Clips, Prompts, Vehicle Lengths, and the 1.2 g Threshold

**Research date:** October 30, 2026  
**Scope:** Research and source evaluation only; no code or repository changes.

## Executive summary

I did not verify five clips that satisfy every requested condition at once. The list below gives five useful leads, but only the first two are reasonably close to the requested locked-off lateral pass; the remaining entries are conditional or too brief for a defensible motion measurement. Treat all passage times as visual estimates, not frame-accurate annotations. Pexels labels its footage free under the [Pexels License](https://www.pexels.com/license/); Pixabay labels its video free under its [Content License / terms](https://pixabay.com/service/terms/). Recheck the current terms and the exact download before public or commercial use.

### Video candidates

| # | Source and license | Duration / listed frame rate | Approximate interval with the whole car visible | Vehicle | Fit and caveats |
|---|---|---|---|---|---|
| 1 | [Pexels — Cars Passing on Suburban Road in Autumn](https://www.pexels.com/video/cars-passing-on-suburban-road-in-autumn-36330662/) · [Pexels License](https://www.pexels.com/license/) | 22 s · 23.98 fps · 3840×2160 | About **1.0–1.5 s** for a small gray sedan; other isolated passes appear around 7.5–8.5 s and 9.25–10.0 s. | Small sedan/crossover; make and model not identifiable. | Static roadside view and lateral movement. The wider source contains multiple vehicles at different times, and some close passes are partly cropped; use only the selected isolated pass. |
| 2 | [Pexels — Black and White Urban Street with Passing Cars](https://www.pexels.com/video/black-and-white-urban-street-with-passing-cars-35089647/) · [Pexels License](https://www.pexels.com/license/) | 12 s · 30 fps · 3840×2160 | About **5.0–5.75 s** for a light-colored car crossing laterally. | Compact sedan or small SUV; not identifiable. | One of the closest matches: wide, stable side view, with the selected car fully visible during the estimated interval. Other traffic appears elsewhere in the clip. |
| 3 | [Pexels — Suburban Road with Cars on a Sunny Day](https://www.pexels.com/video/suburban-road-with-cars-on-a-sunny-day-35527369/) · [Pexels License](https://www.pexels.com/license/) | 9 s · 30 fps · 3840×2160 | About **3.0–3.75 s** for a light sedan in the far lane. | Sedan; make and model not identifiable. | Locked wide view, but this is a multi-lane intersection with other vehicles and crossing geometry. Conditional candidate only; isolate the selected pass and inspect for overlap before use. |
| 4 | [Pexels — Urban Cityscape with Passing Car in Winter](https://www.pexels.com/video/urban-cityscape-with-passing-car-in-winter-36330914/) · [Pexels License](https://www.pexels.com/license/) | 17 s · 23.98 fps · 3840×2160 | About **0.8–1.1 s** for a small dark car. | Small sedan; not identifiable. | Fixed distant lateral view, but a roadside rail masks the lower body/wheels and the useful interval is short. Not recommended for a primary measurement example. |
| 5 | [Pixabay — Car, car driving by, vehicle](https://pixabay.com/videos/car-driving-by-vehicle-rain-31625/) · [Pixabay Content License / terms](https://pixabay.com/service/terms/) | 8.13 s · 23.976 fps · 3840×2160 (stream metadata) | Approximately **4.48–4.56 s**; the whole vehicle is visible only briefly. | Dark estate car/crossover; not identifiable. | Static camera and lateral pass, but the complete-car window is too short for reliable acceleration fitting. Treat as a visual smoke-test lead, not a strong evaluation clip. |

The pass intervals above were estimated from sampled frames. They should be checked against the downloaded source at full resolution before a demo or analysis; the estimate uncertainty is at least a few tenths of a second for the sampled Pexels candidates. The low-resolution sampled previews did not reveal a clearly readable plate or face, but that is not a privacy clearance; verify both at full resolution before use. The stock-page frame-rate field describes the listed asset; it does not independently certify the original capture speed. Verify normal-time playback in the exact file variant used.

### Optional speed-change clip

I could not verify an additional clip that simultaneously shows one isolated car, a clear side-on profile, a locked camera, and an unmistakable braking or start-from-rest event. The closest lead is [Pexels — Cars Stopping on a T Road](https://www.pexels.com/video/cars-stopping-on-a-t-road-4791721/): its Pexels page lists 84 seconds, 59.94 fps, 1920×1080, and a free license. A sampled contact sheet shows a stationary viewpoint and stop/turn activity, but cars often approach obliquely or front-on, several vehicles and pedestrians share the scene, and the MP4 variant name says 30 fps. It does **not** count as a strict match; use only if a manual review confirms a clean isolated segment.

## Three Meta AI app prompts

1. **Autumn suburban pass:** “Create an 8-second photorealistic, real-time roadside video from a completely locked tripod camera, wide true side-on profile across a quiet suburban street in late autumn. One ordinary gray compact sedan travels smoothly from the left edge to the right edge at normal road speed; keep the entire car visible, with no pan, tilt, zoom, cuts, or slow motion. Natural daylight, trees and a simple residential background, realistic wheel motion, no readable license plate, no visible faces, no logos.”

2. **Wide urban pass:** “Create a 7-second black-and-white documentary-style street clip, filmed from a fixed tripod at a wide, level, perpendicular side view. One light-colored compact car drives from left to right across the frame at ordinary real-time speed, fully visible from entry to exit. Keep the camera absolutely still; no cuts, zoom, speed ramp, or slow motion. Quiet urban roadside background, natural tire contact and road motion, no readable plates or identifiable faces.”

3. **Gentle stop-and-go comparison:** “Create an 8-second realistic roadside clip from a locked-off tripod, broad side-on view of a quiet suburban lane. One mid-size sedan enters from the left, gently brakes to a brief stop near the center, then accelerates smoothly and exits to the right; show the complete vehicle throughout, at real-time speed. No camera movement, cuts, zoom, or slow motion; simple daylight background, no other moving vehicles, no readable plate, no visible faces or logos.”

## Representative U.S. vehicle lengths

These are **example model-year/trim dimensions**, not universal lengths for every version of each nameplate. The list is a practical reference set of common U.S. vehicles and includes the examples requested; it is not a strict sales-rank top ten. Lengths are converted using 1 inch = 0.0254 m. The [2025 U.S. sales roundup from Car and Driver](https://www.caranddriver.com/news/g64457986/bestselling-cars-2025/) provides context for the popularity of nameplates such as Camry, Tacoma, Civic, Corolla, Equinox, and Tesla Model Y; Tesla sales are estimates in that roundup.

| Vehicle (specified year/trim) | Published length | Length (m) | Dimension source |
|---|---:|---:|---|
| Ford F-150 Police Responder (2024) | 231.7 in | **5.885** | [Ford Police Vehicles](https://www.ford.com/police-vehicles/f150-police-truck/) |
| Toyota Camry LE FWD (2025) | 193.5 in | **4.915** | [Toyota 2025 Camry brochure](https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/my25-camry-ebrochure.pdf) |
| Honda Civic LX Sedan (2025) | 184.8 in | **4.694** | [Honda 2025 Civic Sedan specifications](https://hondanews.com/en-US/honda-automobiles/releases/release-c28e8d1efb94e520fef21ff3f800cb30-2025-honda-civic-sedan-specifications-features) |
| Toyota RAV4 XLE gas (2024) | 180.9 in | **4.595** | [Toyota 2024 RAV4 brochure](https://www.toyota.com/content/dam/toyota/brochures/pdf/2024/rav4_ebrochure.pdf) |
| Honda CR-V EX-L (2026) | 184.8 in | **4.694** | [Honda 2026 CR-V specifications](https://automobiles.honda.com/2026/cr-v/specs-features-trim-comparison) |
| Toyota Corolla LE Sedan (2025) | 182.3 in | **4.630** | [Toyota 2025 Corolla brochure](https://www.toyota.com/content/dam/toyota/brochures/pdf/2025/corolla_ebrochure.pdf) |
| Toyota Tacoma SR5 Double Cab, 5-ft bed (2024) | 213.0 in | **5.410** | [Toyota 2024 Tacoma brochure](https://www.toyota.com/content/dam/toyota/brochures/pdf/2024/tacoma_ebrochure.pdf) |
| Tesla Model 3 RWD / Long Range (2024+) | 4,720 mm | **4.720** | [Tesla Model 3 Owner’s Manual — dimensions](https://www.tesla.com/ownersmanual/model3/en_us/GUID-56562137-FC31-4110-A13C-9A9FC6657BF0.html) |
| Tesla Model Y RWD (2026) | 188.7 in | **4.793** | [Tesla Model Y](https://www.tesla.com/modely) |
| Chevrolet Equinox FWD LT (2025) | 183.2 in | **4.653** | [Edmunds 2025 Equinox specs](https://www.edmunds.com/chevrolet/equinox/2025/features-specs/) |

The F-150 entry is a specific fleet configuration, not a claim that every F-150 has that length. Truck bed/cab combinations and other trim differences can change the value materially. For calibration, select the exact vehicle configuration when known; otherwise record the length assumption and its uncertainty rather than treating a nameplate-level average as exact.

## Why 1.2 g is a defensible screening threshold — with limits

1. The [Federal Highway Administration’s pavement-friction primer](https://highways.dot.gov/sites/fhwa.dot.gov/files/2023-06/FHWA%20Pavement%20Friction%20for%20Road%20Safety%20Primer.pdf) explains that tire–pavement friction enables braking and acceleration and changes with surface texture, water, and road conditions, so no single g value is a universal physical boundary.
2. [NHTSA’s light-vehicle ABS test-track study](https://www.nhtsa.gov/sites/nhtsa.gov/files/nhtsaabst4finalrpt.pdf) compares full-pedal stops over dry, wet, grass, and gravel surfaces, showing that emergency-braking performance depends on the surface and test conditions rather than one fixed deceleration value.
3. In [MotorTrend’s instrumented 2020 Porsche Taycan Turbo S test](https://www.motortrend.com/reviews/porsche-taycan-turbo-s-drag-test), launch control produced a reported peak of **1.11 g** longitudinal acceleration; its reported **103 ft** 60–0 mph stop corresponds to about **1.17 g average deceleration** under a constant-deceleration calculation, not a measured peak. This exceptional performance-car example puts 1.2 g near the edge of a high-performance reference, not beyond the laws of physics.

**Interpretation:** 1.2 g is a reasonable configurable upper screening threshold for ordinary road-motion examples, but it is not a universal impossibility limit. Peak acceleration and interval-average acceleration are different quantities, and real results depend on tire grip, pavement, weather, slope, vehicle setup, and the quality of the image-derived scale and timing.

## Method and limitations for demo use

The working assumption is one road vehicle observed from a fixed camera, with a known or assumed body length used as a scale reference. Perspective, vehicle yaw, camera movement, lens distortion, lane elevation, inaccurate timestamps, partial occlusion, and a wrong trim-specific vehicle length can all bias the estimated speed and acceleration. A “consistent” or “inconsistent” result should therefore be presented as a physical-motion comparison under stated assumptions, not as a universal conclusion about the source clip.
