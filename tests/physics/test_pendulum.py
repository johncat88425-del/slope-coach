import math

import pytest

from physics.errors import PhysicsInputError
from physics.experiments.pendulum import check_pendulum


def swing(L=0.5, fps=60, seconds=4.0, amp=80.0, decay=0.1, chirp=0.0):
    w = math.sqrt(9.81 / L)
    ts = [i / fps for i in range(int(seconds * fps))]
    xs = [300 + amp * math.exp(-decay * t) * math.sin(w * t * (1 + chirp * t)) for t in ts]
    return ts, xs


def test_real_pendulum_consistent_and_length_recovered():
    ts, xs = swing()
    c = check_pendulum(ts, xs, length_m=0.5)
    assert c.verdict == "consistent", c.reasons
    assert c.period_s == pytest.approx(2 * math.pi * math.sqrt(0.5 / 9.81), rel=0.01)
    assert c.implied_length_m == pytest.approx(0.5, rel=0.02)


def test_wrong_length_and_drifting_period_flagged():
    ts, xs = swing()
    assert check_pendulum(ts, xs, length_m=1.2).verdict == "inconsistent"
    ts, xs = swing(chirp=0.15)
    c = check_pendulum(ts, xs)
    assert c.verdict == "inconsistent" and "varies" in c.reasons[0]


def test_refusals():
    ts, xs = swing(seconds=1.0)
    assert check_pendulum(ts, xs).verdict == "insufficient_data"
    with pytest.raises(PhysicsInputError):
        check_pendulum([0, 1], [0, 1])
    with pytest.raises(PhysicsInputError):
        check_pendulum(*swing(), length_m=-1)
