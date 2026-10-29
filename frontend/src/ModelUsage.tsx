import type {AuditOut} from './audit.js';
import {Localize} from './i18n.js';
export function modelUsage(a:AuditOut,interview?:'model'|'mock'|null){return [
 ['Questions',interview==='model'?'Muse Spark':interview==='mock'?'Prepared questions (no model)':'Not recorded for this result'],
 ['Tracking',a.track_source==='sam'?'SAM 3.1':a.track_source==='manual'?'Manual observations — no model used':a.track_source==='color'?'Colour-based tracking (no model)':'Motion-based tracking (no model)'],
 ['Explanation',a.explanation?.source==='model'?'Muse Spark':a.explanation?.source==='template'?'Prepared explanation (no model)':'Not supplied — no model output shown'],
 ['Headline',a.headline?'Muse Spark':'Not supplied — no model output shown']
 ] as const}
export function ModelUsage({audit,interviewSource}:{audit:AuditOut;interviewSource?:'model'|'mock'|null}){return <Localize><aside data-testid="model-usage"><h3>Meta models used for this result</h3><dl>{modelUsage(audit,interviewSource).map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><p>Code calculates the measurements and checks the motion.</p></aside></Localize>}
