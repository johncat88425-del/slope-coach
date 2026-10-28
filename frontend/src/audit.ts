export type AuditVerdict='consistent'|'inconsistent'|'insufficient_data';
export type AuditOut={audit_id:string;created_at:string;assumed_model:'free_flight';t_start:number;t_end:number;camera_static:boolean;object_size_m:number|null;video_url:string;overlay_url:string|null;track_source:'frame_diff'|'sam'|'manual';verdict:AuditVerdict;reasons:string[];numbers:Record<string,number>;points:[number,number,number][];events:{kind:string;t_s:number;detail:string}[];limits:string[]};
export function verdictText(verdict:AuditVerdict){return {consistent:'與自由落體模型一致',inconsistent:'與自由落體模型不一致',insufficient_data:'與自由落體模型無法判斷'}[verdict]}
export function validateAuditInput(start:string,end:string,size:string){const errors:string[]=[];
 if(!start.trim()||!end.trim()||!Number.isFinite(Number(start))||!Number.isFinite(Number(end))||Number(start)<0||Number(end)<=Number(start))errors.push('時間窗必須為有限秒數，且 0 ≤ 開始 < 結束。');
 if(size.trim()&&(!Number.isFinite(Number(size))||Number(size)<=0))errors.push('物體尺寸必須大於零，單位為米；未知時請留空。');return errors}
