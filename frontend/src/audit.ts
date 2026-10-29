export type AuditModel='free_flight'|'bounce'|'pendulum';
export type AuditVerdict='consistent'|'inconsistent'|'insufficient_data';
export type AuditOut={audit_id:string;created_at:string;object_name?:string;slow_motion?:boolean|null;assumed_model:AuditModel;t_start:number;t_end:number;camera_static:boolean;object_size_m:number|null;synthetic?:boolean;ghost_points?:[number,number,number][];nearest_body?:string|null;length_m?:number|null;video_url:string;overlay_url:string|null;track_source:'frame_diff'|'sam'|'manual';verdict:AuditVerdict;reasons:string[];numbers:Record<string,number>;points:[number,number,number][];events:{kind:string;t_s:number;detail:string}[];limits:string[]};
export function verdictText(verdict:AuditVerdict,model:AuditModel='free_flight') {const name=model==='bounce'?'彈跳':model==='pendulum'?'單擺':'自由落體';return {consistent:`與${name}模型一致`,inconsistent:`與${name}模型不一致`,insufficient_data:`與${name}模型無法判斷`}[verdict]}
export function validateAuditInput(start:string,end:string,size:string){const errors:string[]=[];
 if(!start.trim()||!end.trim()||!Number.isFinite(Number(start))||!Number.isFinite(Number(end))||Number(start)<0||Number(end)<=Number(start))errors.push('時間窗必須為有限秒數，且 0 ≤ 開始 < 結束。');
 if(size.trim()&&(!Number.isFinite(Number(size))||Number(size)<=0))errors.push('物體尺寸必須大於零，單位為米；未知時請留空。');return errors}

/** Validate saved API output without inferring or recomputing measurements. */
export function parseSavedAudit(text:string):AuditOut {
 const a=JSON.parse(text); const finite=(v:unknown)=>typeof v==='number'&&Number.isFinite(v);
 const strings=(v:unknown)=>Array.isArray(v)&&v.every(s=>typeof s==='string');
 if(!a || typeof a!=='object' || typeof a.audit_id!=='string' || typeof a.created_at!=='string'
 || !['free_flight','bounce','pendulum'].includes(a.assumed_model) || !finite(a.t_start) || !finite(a.t_end) || a.t_start<0 || a.t_end<=a.t_start
 || typeof a.camera_static!=='boolean' || !(a.object_size_m===null || finite(a.object_size_m)&&a.object_size_m>0)
 || (a.slow_motion!==undefined && a.slow_motion!==null && typeof a.slow_motion!=='boolean')
 || (a.object_name!==undefined && typeof a.object_name!=='string')
 || (a.synthetic!==undefined && typeof a.synthetic!=='boolean')
 || (a.length_m!==undefined && a.length_m!==null && (!finite(a.length_m)||a.length_m<=0))
 || typeof a.video_url!=='string' || !(a.overlay_url===null || typeof a.overlay_url==='string')
 || !['frame_diff','sam','manual'].includes(a.track_source) || !['consistent','inconsistent','insufficient_data'].includes(a.verdict)
 || !strings(a.reasons) || !strings(a.limits) || !a.numbers || Array.isArray(a.numbers) || typeof a.numbers!=='object' || !Object.values(a.numbers).every(finite)
 || !Array.isArray(a.points) || a.points.length>100000 || !a.points.every((p:unknown)=>Array.isArray(p)&&p.length===3&&p.every(finite))
 || (a.ghost_points!==undefined && (!Array.isArray(a.ghost_points)||a.ghost_points.length>100000||!a.ghost_points.every((p:unknown)=>Array.isArray(p)&&p.length===3&&p.every(finite))))
 || (a.nearest_body!==undefined && a.nearest_body!==null && typeof a.nearest_body!=='string')
 || !Array.isArray(a.events) || !a.events.every((e:any)=>e&&typeof e.kind==='string'&&finite(e.t_s)&&typeof e.detail==='string'))
 throw new Error('Invalid saved audit JSON (supported motion model required).');
 return a as AuditOut;
}
