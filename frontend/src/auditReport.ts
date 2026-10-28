import type {AuditOut} from './audit';
function escape(value:unknown){return String(value).replace(/\|/g,'\\|').replace(/[\r\n]+/g,' ')}
export function auditMarkdown(a:AuditOut){
 const lines=['# Video motion audit','','Result is relative to the stated motion model.','',`- Audit: ${escape(a.audit_id)}`,`- Created: ${escape(a.created_at)}`,`- Model: ${escape(a.assumed_model)}`,`- Verdict: ${escape(a.verdict)}`,`- User-confirmed window: ${a.t_start}–${a.t_end} s`,`- Camera fixed (user): ${a.camera_static}`,`- Object size (user, m): ${a.object_size_m??'not provided'}`,`- Tracking source: ${escape(a.track_source)}`,'','## Reasons','',...a.reasons.map(r=>'- '+escape(r)),'','## Backend numbers (unchanged)','','| Field | Value |','| --- | --- |',...Object.entries(a.numbers).map(([k,v])=>`| ${escape(k)} | ${String(v)} |`),'','## Observed track','','| t_s | x_px | y_px |','| --- | --- | --- |',...a.points.map(([t,x,y])=>`| ${t} | ${x} | ${y} |`),'','## Tracking events','',...a.events.map(e=>`- ${e.t_s} s · ${escape(e.kind)}: ${escape(e.detail)}`),'','## Limits','',...a.limits.map(l=>'- '+escape(l)),'',`Video path: ${escape(a.video_url)}`,`Overlay path: ${escape(a.overlay_url??'not available')}`,''];
 return lines.join('\n');
}
export function downloadText(content:string,name:string,type='text/markdown;charset=utf-8'){
 const href=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=href;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(href),1000);
}
