"""T244: background shift measurement and compensation on synthetic shaky clips."""
import numpy as np
from scipy import ndimage

from physics.camera_motion import compensate, measure_camera_motion
from physics.experiments.freefall import check_flight, fit_flight

H, W, FPS, M_PER_PX = 270, 480, 30.0, 0.01


def _norm(a):
    return (a - a.mean()) / a.std()


def _clip(shake, zoom=False, plain=False, seed=0):
    rng = np.random.default_rng(seed)
    big = 128 + 40 * _norm(ndimage.gaussian_filter(rng.random((H + 80, W + 80)), 2)) if not plain else np.full((H + 80, W + 80), 128.0)
    frames, pts = [], []
    n = 24
    for i in range(n):
        t = i / FPS
        x, y = 60 + 250 * t, 60 - 300 * t + 0.5 * (9.81 / M_PER_PX) * t * t
        sx, sy = shake[i]
        bg = ndimage.shift(big, (sy, sx), order=1)[40:40 + H, 40:40 + W]
        if zoom:
            bg = ndimage.zoom(big, 1 + 0.01 * i, order=1)[40:40 + H, 40:40 + W]
        yy, xx = np.mgrid[0:H, 0:W]
        f = bg.copy()
        f[(xx - (x + sx)) ** 2 + (yy - (y + sy)) ** 2 <= 49] = 0
        frames.append(f)
        pts.append((t, x + sx, y + sy))
    return np.array(frames), pts


def _g(points):
    fit = fit_flight(points)
    return check_flight(fit, m_per_px=M_PER_PX)


def test_shake_is_measured_and_removed():
    rng = np.random.default_rng(1)
    shake = np.cumsum(rng.normal(0, 1.5, (24, 2)), axis=0)
    shake[0] = 0
    frames, pts = _clip(shake)
    raw = _g(pts)
    m = measure_camera_motion(frames, list(range(24)), [(x, y) for _, x, y in pts], 14)
    assert m.reliable and m.translational
    err = np.abs(np.array(m.shifts) - shake).max()
    assert err < 0.6, err
    fixed = _g(compensate(pts, m))
    assert fixed.verdict == "consistent", (raw, fixed)
    assert abs(fixed.g_apparent_m_s2 - 9.81) < 0.3


def test_still_camera_reads_no_shift():
    frames, pts = _clip(np.zeros((24, 2)))
    m = measure_camera_motion(frames, list(range(24)), [(x, y) for _, x, y in pts], 14)
    assert m.reliable and m.max_shift_px < 0.3


def test_plain_background_is_not_reliable():
    frames, pts = _clip(np.zeros((24, 2)) + np.arange(24)[:, None] * 0.5, plain=True)
    m = measure_camera_motion(frames, list(range(24)), [(x, y) for _, x, y in pts], 14)
    assert not m.reliable


def test_zoom_is_not_called_a_shift():
    frames, pts = _clip(np.zeros((24, 2)), zoom=True)
    m = measure_camera_motion(frames, list(range(24)), [(x, y) for _, x, y in pts], 14)
    assert not m.translational
