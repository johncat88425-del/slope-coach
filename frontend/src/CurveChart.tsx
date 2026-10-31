import { Localize } from './i18n.js';
import type { Comparison, Prediction, Trial } from './api';
export function CurveChart({ prediction, trial, comparison }: {
    prediction: Prediction;
    trial?: Trial;
    comparison?: Comparison;
}) {
    const s0 = comparison?.fit?.s0_m;
    const observed = trial && trial.t0_s !== null && s0 !== undefined ? trial.samples.map(s => ({ t: s.t_s - trial.t0_s!, s: s.s_m === null ? null : s.s_m - s0, ok: s.quality === 'ok' })) : [];
    const pts = observed.filter(p => p.t >= 0 && p.ok && p.s !== null);
    const xmax = Math.max(0.01, ...prediction.curve.map(p => p[0]), ...pts.map(p => p.t));
    const ymin = Math.min(0, ...pts.map(p => p.s!));
    const ymax = Math.max(0.01, ...prediction.curve.map(p => p[1]), ...pts.map(p => p.s!));
    const x = (v: number) => 50 + v / xmax * 570, y = (v: number) => 230 - (v - ymin) / (ymax - ymin) * 200;
    let path = '', gap = true;
    for (const p of observed) {
        if (!p.ok || p.s === null || p.t < 0) {
            gap = true;
            continue;
        }
        path += `${gap ? 'M' : 'L'}${x(p.t)},${y(p.s)} `;
        gap = false;
    }
    return <Localize>{<figure data-testid="comparison-chart"><figcaption>後端計算曲線 · 時間從起滑起算（s），位置相對釋放點（m）</figcaption><svg viewBox="0 0 650 270" role="img" aria-label="預測青色虛線，實測橘色實線；不可靠或缺失區段斷線">
 <path d="M50 20V230H620" stroke="#777" fill="none"/>
 <polyline points={prediction.curve.map(p => `${x(p[0])},${y(p[1])}`).join(' ')} stroke="var(--color-prediction, #007e91)" strokeWidth="3" strokeDasharray="7 5" fill="none"/>
 <path d={path} stroke="var(--color-observed, #c26319)" strokeWidth="3" fill="none"/>{pts.map((p, i) => <circle key={i} cx={x(p.t)} cy={y(p.s!)} r="2.5" fill="var(--color-observed, #c26319)"/>)}
 <text x="45" y="253">0</text><text x="560" y="253">{xmax.toFixed(2)} s</text><text x="3" y="25">{ymax.toFixed(2)} m</text>
 </svg><p><span className="cyan">┄┄ 預測</span>　<span className="orange">━━ 實測</span>；非 ok 品質不連線。數據來源：後端 physics，實測來源見試驗表。</p><details><summary>Curve data (backend samples)</summary><div className="table-wrap" tabIndex={0} role="region" aria-label="Curve data"><table><caption>Prediction — dashed line; observed — solid line with dots</caption><thead><tr><th>Series</th><th>Time (s)</th><th>Displacement (m)</th><th>Quality</th></tr></thead><tbody>{prediction.curve.map(([t,s],i)=><tr key={'p'+i}><td>Prediction</td><td>{t}</td><td>{s}</td><td>—</td></tr>)}{observed.map((p,i)=><tr key={'o'+i}><td>Observed</td><td>{p.t}</td><td>{p.s ?? 'Missing'}</td><td>{p.ok ? 'ok' : 'Unreliable / missing'}</td></tr>)}</tbody></table></div></details></figure>}</Localize>;
}
