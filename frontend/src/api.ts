export type Pixel = [number, number];
export type ScenePhoto = {photo_id: string; scene_check: {source: 'model'|'mock'; needs_retake: boolean; retake_reasons: string[]}};
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
  constructor(public status:number, message:string) {super(message); this.name='ApiError'}
}
export function createApi(base='', transport:typeof fetch=fetch) {
  const root=base.replace(/\/$/,'');
  async function request<T>(path:string, init:RequestInit={}, text=false):Promise<T> {
    const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),120000);
    try {
      const response=await transport(root+'/api'+path,{...init,signal:controller.signal});
      if(!response.ok) {
        const raw=await response.text(); let message=raw;
        try {const body=JSON.parse(raw); message=typeof body.detail==='string'?body.detail:JSON.stringify(body.detail??body)} catch { /* retain server error text */ }
        throw new ApiError(response.status,message||response.statusText);
      }
      return (text?await response.text():await response.json()) as T;
    } catch(error) {
      if(error instanceof ApiError) throw error;
      if(error instanceof Error && error.name==='AbortError') throw new Error('請求逾時。操作可能已在伺服器完成，請先重新讀取紀錄，不會自動重送。');
      throw new Error('無法連接後端。請確認 http://localhost:8000 與 Vite proxy 已啟動。');
    } finally {clearTimeout(timer)}
  }
  function json<T>(method:string,path:string,body:unknown) {return request<T>(path,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}
  const e=(id:string)=>'/experiments/'+encodeURIComponent(id), t=(id:string)=>'/trials/'+encodeURIComponent(id);
  return {
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
