import math

from physics.experiments.freefall import check_bounces
from physics.persistence import persistence_events
from physics.tracking import Detection


def bouncing(e=0.8, h0=300.0, g=2000.0, fps=120, bounces=3, gain_at=None):
    """Ball dropped from h0 px above the floor (y=400), restitution e; gain_at makes one rebound grow."""
    pts, t, h = [], 0.0, h0
    for k in range(bounces + 1):
        v_up = math.sqrt(2 * g * h)
        t_seg = 2 * v_up / g if k else math.sqrt(2 * h / g)
        n = max(int(t_seg * fps), 2)
        for i in range(n):
            tau = i / fps
            y = (400 - h + 0.5 * g * tau * tau) if k == 0 else (400 - v_up * tau + 0.5 * g * tau * tau)
            pts.append((t + tau, 100 + 50 * (t + tau), min(y, 400)))
        t += t_seg
        h = h * e * e * (2.0 if gain_at == k else 1.0)
    return pts


def test_passive_bounces_are_consistent():
    c = check_bounces(bouncing())
    assert c.verdict == "consistent", c
    assert len(c.heights_px) >= 3
    assert all(r <= 1.0 for r in c.restitution)


def test_rebound_higher_than_drop_is_flagged():
    c = check_bounces(bouncing(gain_at=1))
    assert c.verdict == "inconsistent"
    assert "rebound" in c.reasons[0]


def test_bounce_refuses_short_track():
    assert check_bounces(bouncing()[:5]).verdict == "insufficient_data"


def dets(n=20, vanish=(), big=(), jump=()):
    out = []
    for i in range(n):
        if i in vanish:
            out.append(Detection(i / 30, None))
            continue
        x = 10 * i + (200 if i in jump else 0)
        out.append(Detection(i / 30, (x, 50), area_px=400 * (4 if i in big else 1)))
    return out


def test_persistence_events():
    assert persistence_events(dets()) == []
    kinds = [e.kind for e in persistence_events(dets(vanish=(8, 9, 10), big=(15,), jump=(5,)))]
    assert kinds.count("vanished") == 1 and "size_jump" in kinds and "position_jump" in kinds
    # gaps at the ends of the clip are not events
    assert persistence_events(dets(vanish=(0, 1, 2, 3))) == []
