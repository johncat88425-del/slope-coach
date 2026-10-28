from physics.calibration import Calibration, SlopeGeometry
from physics.tracking import Detection

# 1000 px ruler == 1.0 m; path runs left-to-right along the image x axis
CALIB = Calibration(ruler_px=((0, 0), (1000, 0)), ruler_length_m=1.0,
                    path_start_px=(100, 500), path_end_px=(1100, 500))
GEOM = SlopeGeometry(length_m=1.0, height_m=0.3)


def synthetic_detections(a, v0=0.0, s0=0.05, t0=0.5, fps=30, duration=1.5, noise=None):
    """Slider at rest at s0 until t0, then s0 + v0 t + a t^2 / 2."""
    dets = []
    n = int(duration * fps)
    for i in range(n):
        t = i / fps
        tt = max(t - t0, 0.0)
        s = s0 + v0 * tt + 0.5 * a * tt * tt
        if s > 0.95:
            break
        if noise is not None:
            s += noise[i % len(noise)]
        dets.append(Detection(t, (100 + s * 1000, 500), area_px=400))
    return dets
