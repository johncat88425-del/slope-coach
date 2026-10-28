"""Markdown and CSV export of the whole experiment record, including unresolved questions."""
from __future__ import annotations

import csv
import io

from .store import ExperimentRecord, store


def to_markdown(exp: ExperimentRecord) -> str:
    lines = [f"# {exp.title}", "", f"Experiment `{exp.experiment_id}`, created {exp.created_at.isoformat()}", ""]
    lines += ["## Calibrations", ""]
    for c in exp.calibrations:
        lines.append(f"- v{c['version']} ({c['reason']}): L = {c['slope_length_m']} m, h = {c['slope_height_m']} m, "
                     f"angle {c['angle_deg']:.2f} deg, user-confirmed")
    lines += ["", "## Baselines", ""]
    for b in exp.baselines:
        lines.append(f"- v{b['version']}: mu_eff = {b['mu_eff']:.3f} ± {b['mu_spread']:.3f} from {len(b['trial_ids'])} trials")
    lines += ["", "## Predictions (locked before the trial they were compared with)", ""]
    for p in exp.predictions.values():
        lines.append(f"- `{p['prediction_id']}` at {p['created_at'].isoformat()}: predicted arrival "
                     f"{p['params']['t_end_s']:.3f} s over {p['params']['distance_m']} m; assumptions: {'; '.join(p['assumptions'])}")
    lines += ["", "## Comparisons", ""]
    for c in exp.comparisons.values():
        err = c["arrival_error_rel"]
        lines.append(f"- `{c['comparison_id']}`: {c['verdict']}"
                     + (f", arrival error {err:+.1%} (tolerance {c['tolerance_rel']:.0%})" if err is not None else ""))
        for chk in c["checks"]:
            if not chk["passed"]:
                lines.append(f"  - check failed: {chk['name']}: {chk['detail']}")
        for ev in c["evidence"]:
            lines.append(f"  - {ev['candidate']}: {ev['finding']} (cannot distinguish: {ev['cannot_distinguish']})")
        for said in c["can_still_say"]:
            lines.append(f"  - still known: {said}")
    lines += ["", "## Next checks", ""]
    for i in exp.interventions.values():
        lines.append(f"- {i['check_type']} chosen by {i['chosen_by']}; result trial: {i['result_trial_id'] or 'not yet recorded'}")
    lines += ["", "## Trials", ""]
    for tid in exp.trial_ids:
        t = store.trials[tid]
        manual = sum(s.source == "manual" for s in t.samples)
        usable = sum(s.usable for s in t.samples)
        lines.append(f"- `{tid}` ({t.kind}): {usable}/{len(t.samples)} usable frames, {manual} manually placed, "
                     f"release time {t.t0_s if t.t0_s is not None else 'not confirmed'}")
    return "\n".join(lines) + "\n"


def to_csv(exp: ExperimentRecord) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["trial_id", "kind", "t_s", "s_m", "quality", "source"])
    for tid in exp.trial_ids:
        t = store.trials[tid]
        for s in t.samples:
            w.writerow([tid, t.kind, f"{s.t_s:.4f}", "" if s.s_m is None else f"{s.s_m:.5f}", s.quality.value, s.source])
    return buf.getvalue()
