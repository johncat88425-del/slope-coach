import {DEMO_ONLY,demoUploadMessage} from './mode.js';
import type {VehicleClass} from './vehiclePresentation.js';
import type {AuditModel,AuditOut} from './audit';
export type FlightWindows={draft_id:string;source:'physics';track_source:'frame_diff'|'color';windows:{t_start:number;t_end:number}[];scanned_until_s:number};
export type SampleClip={name:string;kind:'generated'|'synthetic';label:string};
export function parseSampleClips(value:unknown):SampleClip[]{
 if(!Array.isArray(value)||!value.every(row=>row&&typeof row.name==='string'&&row.name.trim()&&typeof row.label==='string'&&row.label.trim()&&['generated','synthetic'].includes(row.kind)))throw new Error('The sample list is invalid. Please try again.');
 return value;
}
export type InterviewField='camera_static'|'slow_motion'|'object_size_m'|'time_window'|'assumed_model'|'length_m';
export type VoiceField={value:boolean|number|string|number[];confirmed:false};
export type VoiceAnswer={source:{transcript:string;fields:string};transcript:string;fields:Partial<Record<InterviewField,VoiceField>>};
export type ObjectSuggestion={source:string;object_name:string;camera_looks_static:boolean|null;reason:string;assumed_model?:'vehicle'|null;judgeable?:boolean|null;vehicle_class?:VehicleClass|null};
export type AuditDraft={draft_id:string;video_url:string;interview:{source:'model'|'mock';note?:string|null;questions:{field:InterviewField|'vehicle_class';text:string}[]};suggestion?:ObjectSuggestion|null};
export type InterviewAnswers={object_name?:string;t_start:number;t_end:number;camera_static:boolean;slow_motion?:boolean;assumed_model:AuditModel;object_size_m?:number;length_m?:number;vehicle_class?:VehicleClass};
export type Pixel = [number, number];
export type ScenePhoto = {photo_id: string; photo_url?: string|null; scene_check: {source: 'model'|'mock'; needs_retake: boolean; retake_reasons: string[]}};
export type CalibrationInput = {ruler_px: [Pixel,Pixel]; ruler_length_m: number; path_start_px: Pixel; path_end_px: Pixel; slope_length_m: number; slope_height_m: number; reason?: string};
export type Calibration = CalibrationInput & {version:number; m_per_px:number; angle_deg:number; created_at:string};
export type Detection = {t_s:number; centroid_px:Pixel|null; area_px?:number; source:'sam'|'manual'};
export type Sample = {t_s:number; s_m:number|null; quality:string; source:string};
export type TrialKind = 'baseline'|'test'|'intervention';
export type Trial = {trial_id:string; kind:TrialKind; calibration_version:number; uploaded_at:string; video_url:string|null; t0_s:number|null; t0_source:'user'|null; samples:Sample[]; usable_fraction:number; manual_frames:number};
export type Baseline = {version:number; calibration_version:number; trial_ids:string[]; mu_eff:number; mu_spread:number; accel_mean_m_s2:number; accel_spread_m_s2:number; created_at:string};
export type Prediction = {prediction_id:string; calibration_version:number; baseline_version:number; created_at:string; locked:true; params:Record<string,number>; assumptions:string[]; curve:[number,number][]; overlay_px:[number,number,number][]};
export type Evidence = {candidate:'dimension_check'|'release_check'; finding:string; numbers:Record<string,number>; cannot_distinguish:string};
export type Comparison = {comparison_id:string; prediction_id:string; trial_id:string; verdict:'consistent'|'discrepancy'|'insufficient_data'; checks:{name:string;passed:boolean;detail:string;blocking:boolean}[]; fit:Record<string,number>|null; predicted_arrival_s:number|null; observed_arrival_s:number|null; arrival_error_rel:number|null; tolerance_rel:number; residuals:[number,number][]; can_still_say:string[]; evidence:Evidence[];created_at:string};
export type Intervention = {intervention_id:string;comparison_id:string;check_type:string;instructions:Record<string,string|string[]>;chosen_by:string;model_rationale:string|null;result_trial_id:string|null;created_at:string};
export type ExperimentRecord = {experiment_id:string;title:string;created_at:string;scene_photos:ScenePhoto[];calibrations:Calibration[];trials:Trial[];baselines:Baseline[];predictions:Prediction[];comparisons:Comparison[];interventions:Intervention[]};
export class ApiError extends Error {
  constructor(public status:number, message:string,public temporary=false) {super(message); this.name='ApiError'}
}
export const serverBusyMessage='The server is starting or busy. Please wait one minute and try again.';
export const requestTimeoutMessage='This check took too long. Select a shorter time window (0.5–2 seconds) and try again.';
const looksLikeHtml=(text:string)=>/<(?:!doctype\b|!--|\/?[a-z][\w:-]*(?:\s|\/?>))|&lt;\/?(?:html|body|head)\b/i.test(text);
function isHtmlResponse(raw:string,contentType:string|null){
 if(/\b(?:text\/html|application\/xhtml\+xml)\b/i.test(contentType??''))return true;
 try{JSON.parse(raw);return false}catch{return /^\s*(?:<|&lt;)/i.test(raw)&&looksLikeHtml(raw)}
}
export function isTemporaryApiError(error:unknown):boolean {
 const message=error instanceof Error?error.message:typeof error==='string'?error:'';
 return (error instanceof ApiError&&(error.temporary||[502,503,504].includes(error.status)))||message===serverBusyMessage||looksLikeHtml(message);
}
export function friendlyApiError(error:unknown):string {
 if(isTemporaryApiError(error))return serverBusyMessage;
 if(error instanceof ApiError&&[429,413].includes(error.status)&&error.message.trim())return error.message;
 if(error instanceof ApiError){const prefix=error.status===404?'Result not found. Check the ID or load a saved JSON.':error.status===422?'Please check the submitted settings.':'The backend could not complete this request.';return error.message.trim()?prefix+' Reason: '+error.message:prefix}
 return error instanceof Error ? error.message : String(error);
}
function backendError(status:number,raw:string,contentType:string|null=null){
 let message=raw;try{const body=JSON.parse(raw);message=typeof body.detail==='string'?body.detail:JSON.stringify(body.detail??body)}catch{}
 const temporary=[502,503,504].includes(status)||isHtmlResponse(raw,contentType)||looksLikeHtml(message);
 return new ApiError(status,temporary?serverBusyMessage:message||'Request failed',temporary);
}
export type UploadProgress=(percent:number|null)=>void;
export function uploadAudit(url:string,data:FormData,progress:UploadProgress,makeXhr:()=>XMLHttpRequest=()=>new XMLHttpRequest()):Promise<AuditOut>{
 return new Promise((resolve,reject)=>{const xhr=makeXhr();xhr.open('POST',url);xhr.timeout=360000;
 xhr.upload.onprogress=e=>progress(e.lengthComputable&&e.total>0?Math.min(100,Math.round(e.loaded/e.total*100)):null);
 xhr.upload.onload=()=>progress(100);
 xhr.onload=()=>{const contentType=xhr.getResponseHeader?.('Content-Type')??null;if(xhr.status<200||xhr.status>=300||isHtmlResponse(xhr.responseText,contentType)){reject(backendError(xhr.status,xhr.responseText,contentType));return}try{resolve(JSON.parse(xhr.responseText))}catch{reject(new Error('The server returned an unreadable result. Please try again.'))}};
 xhr.onerror=()=>reject(new Error('Cannot connect to the server. Check your connection and try again.'));
 xhr.ontimeout=()=>reject(new Error(requestTimeoutMessage));
 xhr.onabort=()=>reject(new Error('Upload was interrupted. No automatic retry was made.'));
 progress(0);xhr.send(data);
 });
}
export const jobLostMessage='The free server restarted while checking this clip, so the result was lost. Please submit it again.';
export function createApi(base='', transport:typeof fetch=fetch,options:{demoOnly?:boolean,pollMs?:number}={}) {
  const demoOnly=options.demoOnly??DEMO_ONLY;
  const pollMs=options.pollMs??3000;
  const root=base.replace(/\/$/,'');
  async function request<T>(path:string, init:RequestInit={}, text=false):Promise<T> {
    if(demoOnly)throw new Error(demoUploadMessage);
    const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),360000);
    try {
      const response=await transport(root+'/api'+path,{...init,signal:controller.signal});
      const raw=await response.text(),contentType=response.headers.get('Content-Type');
      if(!response.ok||isHtmlResponse(raw,contentType))throw backendError(response.status,raw,contentType);
      return (text?raw:JSON.parse(raw)) as T;
    } catch(error) {
      if(error instanceof ApiError) throw error;
      if(error instanceof Error && error.name==='AbortError') throw new Error(requestTimeoutMessage);
      throw new Error('Cannot connect to the server. Check your connection and try again.');
    } finally {clearTimeout(timer)}
  }
  function json<T>(method:string,path:string,body:unknown) {return request<T>(path,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
  // T246: a check runs as a background job on the server; poll it so a slow check never loses its result.
  async function waitForJob(started:unknown):Promise<AuditOut>{
    const job=started as {job_id?:string};
    if(!job||typeof job.job_id!=='string')return started as AuditOut; // older backend answered with the result itself
    let misses=0;
    for(;;){
      await new Promise(r=>setTimeout(r,pollMs));
      let state:{status:string,audit?:AuditOut,error?:string,status_code?:number};
      try{state=await request('/audit-jobs/'+encodeURIComponent(job.job_id));misses=0}
      catch(error){
        if(error instanceof ApiError&&error.status===404)throw new ApiError(404,jobLostMessage);
        if(error instanceof ApiError&&!error.temporary)throw error;
        if(++misses>=5)throw error;continue;
      }
      if(state.status==='done'&&state.audit)return state.audit;
      if(state.status==='failed')throw new ApiError(state.status_code??500,state.error||'The check failed.');
    }
  }
  const e=(id:string)=>'/experiments/'+encodeURIComponent(id), t=(id:string)=>'/trials/'+encodeURIComponent(id);
  return {
    audit:(file:File,t_start:number,t_end:number,camera_static:boolean,object_size_m?:number,assumed_model:AuditModel='free_flight',onProgress?:UploadProgress,length_m?:number,object_name='ball',slow_motion?:boolean,vehicle_class?:VehicleClass)=>{if(demoOnly)return Promise.reject(new Error(demoUploadMessage));const data=new FormData();data.append('file',file);data.append('object_name',object_name.trim()||'ball');if(slow_motion!==undefined)data.append('slow_motion',String(slow_motion));data.append('t_start',String(t_start));data.append('t_end',String(t_end));data.append('camera_static',String(camera_static));data.append('assumed_model',assumed_model);if(assumed_model==='vehicle'&&vehicle_class)data.append('vehicle_class',vehicle_class);if(object_size_m!==undefined)data.append('object_size_m',String(object_size_m));if(length_m!==undefined)data.append('length_m',String(length_m));return (onProgress?uploadAudit(root+'/api/audit-jobs',data,onProgress):request<unknown>('/audit-jobs',{method:'POST',body:data})).then(waitForJob)},
    flightWindows:(id:string,object_name:string)=>{const body=new FormData();body.append('object_name',object_name.trim()||'ball');return request<FlightWindows>('/audit-drafts/'+encodeURIComponent(id)+'/windows',{method:'POST',body})},
    auditDraft:(file:File)=>{const data=new FormData();data.append('file',file);return request<AuditDraft>('/audit-drafts',{method:'POST',body:data})},
    sampleClips:async()=>parseSampleClips(await request<unknown>('/samples')),
    sampleDraft:(name:string)=>request<AuditDraft>('/samples/'+encodeURIComponent(name)+'/draft',{method:'POST'}),
    voiceAnswer:(id:string,audio:File)=>{const body=new FormData();body.append('audio',audio);return request<VoiceAnswer>('/audit-drafts/'+encodeURIComponent(id)+'/voice',{method:'POST',body})},
    auditFromDraft:(id:string,answers:InterviewAnswers)=>{const data=new FormData();data.append('draft_id',id);for(const [k,v] of Object.entries(answers))if(v!==undefined)data.append(k,String(v));return request<unknown>('/audit-jobs',{method:'POST',body:data}).then(waitForJob)},
    spend:()=>request<unknown>('/spend'),
    getAudit:(id:string)=>request<AuditOut>('/audits/'+encodeURIComponent(id)),
    create:(title:string)=>json<ExperimentRecord>('POST','/experiments',{title}),
    get:(id:string)=>request<ExperimentRecord>(e(id)),
    photo:(id:string,file:File)=>{const data=new FormData();data.append('file',file);return request<ScenePhoto>(e(id)+'/scene-photo',{method:'POST',body:data})},
    calibration:(id:string,body:CalibrationInput)=>json<Calibration>('POST',e(id)+'/calibrations',body),
    trial:(id:string,kind:TrialKind,version:number,file:File)=>{const data=new FormData();data.append('kind',kind);data.append('calibration_version',String(version));data.append('file',file);return request<Trial>(e(id)+'/trials',{method:'POST',body:data})},
    track:(id:string)=>request<Trial>(t(id)+'/track?text_prompt='+encodeURIComponent('sliding block'),{method:'POST'}),
    detections:(id:string,detections:Detection[])=>json<Trial>('PUT',t(id)+'/detections',{detections}),
    releaseSuggestion:(id:string)=>request<{source:'model'|'mock';candidate_t0_s:number|null;reason:string}>(t(id)+'/release-suggestion'),
    release:(id:string,t0_s:number)=>json<Trial>('PUT',t(id)+'/release-time',{t0_s}),
    baseline:(id:string,trial_ids:string[],calibration_version:number)=>json<Baseline>('POST',e(id)+'/baselines',{trial_ids,calibration_version}),
    predict:(id:string,calibration_version:number,baseline_version:number,distance_m:number)=>json<Prediction>('POST',e(id)+'/predictions',{calibration_version,baseline_version,distance_m}),
    compare:(id:string,prediction_id:string,trial_id:string)=>json<Comparison>('POST',e(id)+'/comparisons',{prediction_id,trial_id}),
    intervene:(id:string,comparison_id:string,check_type:Evidence['candidate'])=>json<Intervention>('POST',e(id)+'/interventions',{comparison_id,check_type,chosen_by:'user'}),
    link:(id:string,result_trial_id:string)=>json<Intervention>('PATCH','/interventions/'+encodeURIComponent(id),{result_trial_id}),
    report:(id:string,format:'md'|'csv')=>request<string>(e(id)+'/report.'+format,{},true),
  };
}
