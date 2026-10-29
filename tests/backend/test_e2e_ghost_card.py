"""tests/backend/test_e2e_ghost_card.py: Backend E2E verification for T68 (Ghost Review & Physics Card)."""

import json
import pathlib
import pytest
from physics.experiments.freefall import fit_flight, ghost_track, nearest_body


def test_ghost_track_and_nearest_body_deterministic():
    m = 0.003
    def pts(g):
        return [(i / 60, 40 + 300 * i / 60, 300 - 600 * i / 60 + 0.5 * (g / m) * (i / 60) ** 2) for i in range(40)]
    
    # Earth normal: ghost aligns with real trajectory
    real = pts(9.81)
    fit_real = fit_flight(real)
    ghost_real = ghost_track(fit_real, [p[0] for p in real], m)
    assert max(abs(g[2] - p[2]) for g, p in zip(ghost_real, real)) < 1.0

    # Slow motion (quarter g): ghost drops much faster than slow observations
    slow = pts(9.81 / 4)
    fit_slow = fit_flight(slow)
    ghost_slow = ghost_track(fit_slow, [p[0] for p in slow], m)
    assert abs(ghost_slow[-1][2] - slow[-1][2]) > 100

    # Nearest body checks
    assert nearest_body(1.7)[0] == "Moon"
    assert nearest_body(9.5)[0] == "Earth"
    assert nearest_body(3.0)[0] == "Mars"


def test_demo_records_contain_ghost_and_physics_card_fields():
    demo_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "data" / "demo"
    assert demo_dir.exists()
    demo_files = list(demo_dir.glob("*.json"))
    assert len(demo_files) >= 6

    for demo_file in demo_files:
        with open(demo_file) as f:
            data = json.load(f)
        assert "ghost_points" in data
        assert "nearest_body" in data
        assert "numbers" in data
        assert "points" in data
        assert "verdict" in data

