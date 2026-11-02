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


def test_long_1080p_window_uses_little_memory():
    """T249: a 5 s window restarted the 512 MB host; frames are now halved one at a time, not stacked as floats."""
    import tracemalloc
    import numpy as np
    from physics.camera_motion import measure_camera_motion
    base = (np.random.default_rng(0).random((1090, 1930)) * 255).astype(np.uint8)
    frames = np.stack([base[i % 8: i % 8 + 1080, :1920] for i in range(30)])
    tracemalloc.start()
    m = measure_camera_motion(frames, list(range(30)), [(500 + 5 * i, 400) for i in range(30)], 30)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert m.reliable and peak < 40e6


def test_roll_and_zoom_are_measured_and_undone():
    """T256: the camera zooms ~11% and rolls ~5 deg while a ball flies; the track is mapped back to frame one."""
    import numpy as np
    from scipy.ndimage import affine_transform, gaussian_filter
    from physics.camera_motion import compensate_similarity, measure_camera_motion
    rng = np.random.default_rng(1)
    H, W, n = 240, 320, 20
    tex = gaussian_filter(rng.random((H * 2, W * 2)), 2) * 255
    frames, truth, seen = [], [], []
    c = np.array([W / 2, H / 2])
    for i in range(n):
        a, b = 0.006 * i, np.radians(0.25 * i)
        m, t = np.array([[1 + a, -b], [b, 1 + a]]), np.array([0.5 * i, -0.3 * i])
        minv = np.linalg.inv(m)
        M = np.array([[minv[1, 1], minv[1, 0]], [minv[0, 1], minv[0, 0]]])
        rc, tt = np.array([H / 2, W / 2]), np.array([t[1], t[0]])
        f = affine_transform(tex, M, offset=rc + np.array([H / 2, W / 2]) - M @ (rc + tt), output_shape=(H, W), order=1)
        ref = np.array([60 + 8 * i, 50 + 0.9 * i * i])
        now = m @ (ref - c) + t + c
        yy, xx = np.mgrid[0:H, 0:W]
        f[(xx - now[0]) ** 2 + (yy - now[1]) ** 2 < 36] = 0
        frames.append(f), truth.append(ref), seen.append((i / 30, now[0], now[1]))
    mo = measure_camera_motion(np.array(frames, dtype=np.float32), list(range(n)), [(x, y) for _, x, y in seen], 10)
    assert mo.reliable and mo.similar and not mo.translational and 0.09 < mo.max_zoom < 0.14
    pts, sizes = compensate_similarity(seen, [12.0] * n, mo, W, H)
    assert max(np.hypot(p[1] - q[0], p[2] - q[1]) for p, q in zip(pts, truth)) < 4  # was 28 px uncorrected
    assert sizes[-1] < sizes[0]  # the zoom's growth in apparent size is taken out
