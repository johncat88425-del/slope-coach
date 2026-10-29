import numpy as np

from backend.video import blob_diameter, color_for, track_color, track_with_sizes

ORANGE, GREY = (240, 140, 40), (90, 90, 90)


def disk(f, cx, cy, r, color):
    yy, xx = np.mgrid[:f.shape[0], :f.shape[1]]
    f[(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = color


def scene(n=20):
    """Orange ball moving right; a static orange block (furniture) and a big moving grey arm."""
    frames = []
    for i in range(n):
        f = np.full((200, 300, 3), 230, np.float32)
        f[150:190, 10:60] = ORANGE  # static, same colour
        f[20:120, 200 + 4 * i:240 + 4 * i] = GREY  # moving, wrong colour, larger than the ball
        disk(f, 40 + 6 * i, 60 + i, 8, ORANGE)
        frames.append(f)
    return np.stack(frames)


def test_color_tracker_follows_the_ball_not_the_arm_or_furniture():
    pts, sizes = track_color(scene(), 30.0, 1.0, "orange")
    assert len(pts) == 20
    for i, (t, x, y) in enumerate(pts):
        assert abs(t - (1.0 + i / 30)) < 1e-9
        assert abs(x - (40 + 6 * i)) < 1.0 and abs(y - (60 + i)) < 1.0
    assert all(abs(d - 16) < 1.5 for d in sizes)


def test_frame_differencing_is_pulled_off_the_ball_by_the_arm():
    gray = scene().mean(axis=-1)
    pts, _ = track_with_sizes(gray, 30.0, 0.0)
    assert any(abs(x - (40 + 6 * i)) > 20 for i, (_, x, _) in enumerate(pts))


def test_blob_diameter_ignores_motion_blur_along_one_axis():
    yy, xx = np.mgrid[:60, :120]
    blur = np.zeros((60, 120), bool)
    for dx in range(0, 30):  # a 16 px disk smeared 30 px to the right
        blur |= (xx - 40 - dx) ** 2 + (yy - 30) ** 2 <= 64
    ys, xs = np.nonzero(blur)
    assert abs(blob_diameter(ys, xs) - 16) < 1.5


def test_colour_comes_only_from_the_human_label():
    assert color_for("orange ball") == "orange"
    assert color_for("Orange ping pong ball") == "orange"
    assert color_for("ball") is None and color_for("") is None


def test_other_named_colours_including_red_across_zero_hue():
    import pytest as _pytest

    for name, rgb in (("yellow", (240, 220, 30)), ("green", (40, 200, 60)), ("blue", (30, 80, 230)),
                      ("red", (230, 30, 40))):
        frames = []
        for i in range(12):
            f = np.full((200, 300, 3), 230, np.float32)
            disk(f, 40 + 6 * i, 60 + i, 8, rgb)
            frames.append(f)
        pts, _ = track_color(np.stack(frames), 30.0, 0.0, name)
        assert len(pts) == 12, name
        assert pts[5][1] == _pytest.approx(70, abs=1.0), name
    assert color_for("yellow tennis ball") == "yellow" and color_for("red ball") == "red"
