"""Scores data/bench/results.csv: real clips judged inconsistent (should never happen), AI clips judged consistent (missed),
refusals, and the share of AI clips caught per generator. Each non-consistent row gets one failure category from its reasons.
usage: python3 scripts/bench_score.py data/bench/results.csv"""
import csv, sys
from collections import Counter, defaultdict

REAL = {"real", "own", "pexels", "physicsiq"}
CATEGORIES = [  # first match wins; the category describes why the check could not or did not judge cleanly
    ("tracking switched object", ("track jumps", "switched to another object")),
    ("frames dropped", ("tracked in only", "frames")),
    ("object toward camera", ("towards or away from the camera", "size changes", "size jumps")),
    ("camera", ("camera is not static", "camera moved", "camera rotated", "too plain to measure")),
    ("no free flight", ("hardly rises or falls", "not distinguishable from zero", "clean parabola", "constant-acceleration path", "points", "deg away from image-down")),
    ("size", ("implied size", "object size")),
]

def category(row):
    if row["verdict"] == "consistent":
        return ""
    text = row["reasons"].lower()
    if row["verdict"] == "inconsistent" and ("apparent g" in text or "different accelerations" in text) and row["source"] not in REAL:
        return "caught (physics)"
    return next((name for name, keys in CATEGORIES if any(k in text for k in keys)), "other")

def main(path):
    rows = list(csv.DictReader(open(path)))
    real = [r for r in rows if r["source"] in REAL]
    ai = [r for r in rows if r["source"] not in REAL]
    pct = lambda n, d: f"{n}/{d} ({100 * n / d:.0f}%)" if d else "0/0"
    print(f"clips: {len(rows)} (real {len(real)}, AI {len(ai)})")
    print("real clips judged inconsistent (false accusation):", pct(sum(r["verdict"] == "inconsistent" for r in real), len(real)))
    print("AI clips judged consistent (missed):", pct(sum(r["verdict"] == "consistent" for r in ai), len(ai)))
    print("refused (cannot judge), all clips:", pct(sum(r["verdict"] == "insufficient_data" for r in rows), len(rows)))
    print("  real refused:", pct(sum(r["verdict"] == "insufficient_data" for r in real), len(real)), " AI refused:", pct(sum(r["verdict"] == "insufficient_data" for r in ai), len(ai)))
    print("AI caught (inconsistent) by generator:")
    by = defaultdict(list)
    for r in ai: by[r["source"]].append(r)
    for src in sorted(by): print(f"  {src:7s} {pct(sum(r['verdict'] == 'inconsistent' for r in by[src]), len(by[src]))}")
    print("failure categories (non-consistent rows):")
    for name, n in Counter(category(r) for r in rows if r["verdict"] != "consistent").most_common(): print(f"  {name}: {n}")
    print("real clips judged inconsistent:", ", ".join(f"{r['clip']} ({r['reasons'][:80]})" for r in real if r["verdict"] == "inconsistent") or "none")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/bench/results.csv")
