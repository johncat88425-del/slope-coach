import type {Calibration,Comparison,Prediction,Trial} from './api';
/** Display-coordinate mapping only; prediction and observed distances are never re-fit here. */
export function overlayFrame(mediaTime:number,prediction:Prediction,trial:Trial,calibration:Calibration,comparison:Comparison){
 const s0=comparison.fit?.s0_m;
 if(trial.t0_s===null||s0===undefined||!Number.isFinite(s0)||calibration.version!==trial.calibration_version||calibration.version!==prediction.calibration_version||comparison.prediction_id!==prediction.prediction_id||comparison.trial_id!==trial.trial_id||!comparison.checks.some(c=>c.name==='calibration'&&c.passed)||!comparison.checks.some(c=>c.name==='release_time'&&c.passed)||!(calibration.m_per_px>0))return null;
 const time=mediaTime-trial.t0_s;if(time<0||time>prediction.params.t_end_s)return null;
 const [ax,ay]=calibration.path_start_px,[bx,by]=calibration.path_end_px;
 const length=Math.hypot(bx-ax,by-ay);if(!length)return null;
 const dx=(bx-ax)/length,dy=(by-ay)/length;
 const point=[...prediction.overlay_px].reverse().find(p=>p[0]<=time);if(!point)return null;
 const predicted:[number,number]=[point[1]+dx*s0/calibration.m_per_px,point[2]+dy*s0/calibration.m_per_px];
 const along=(predicted[0]-ax)*dx+(predicted[1]-ay)*dy;if(along<0||along>length)return null;
 const sample=trial.samples.reduce<typeof trial.samples[number]|undefined>((best,s)=>!best||Math.abs(s.t_s-mediaTime)<Math.abs(best.t_s-mediaTime)?s:best,undefined);
 const observed=sample?.quality==='ok'&&sample.s_m!==null&&Math.abs(sample.t_s-mediaTime)<=0.05?[ax+dx*sample.s_m/calibration.m_per_px,ay+dy*sample.s_m/calibration.m_per_px] as [number,number]:null;
 return {predicted,observed};
}
