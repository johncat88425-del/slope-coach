/** The final recording order; measurement values are read from saved audits. */
export const recordingSteps=[
 {key:'real_own_2',view:'result',title:'A recorded ball, consistent with the model',text:'Review the final saved result from john’s recorded experiment.'},
 {key:'generated_meta_clip4',view:'ghost',title:'A basketball with a different fall',text:'Compare the stored Earth-model path with the tracked path. This replay does not run a new analysis.'},
 {key:'generated_meta_clip2',view:'result',title:'Motion the camera cannot resolve',text:'Review the insufficient-data result and its original capture limitations.'},
 {key:'synthetic_car_50kmh_braking',view:'result',title:'A car braking within the model',text:'Synthetic test clip — program-drawn motion, not a recorded driving experiment.'},
 {key:'synthetic_car_3g_launch',view:'result',title:'A car accelerating outside the model',text:'Synthetic test clip — the saved backend result checks the vehicle model.'},
 {key:'generated_meta_clip4',view:'share',title:'Share the evidence',text:'Download the card with stored measurements, actual sources and the scope of the check.'},
] as const;
export const demoSteps=recordingSteps;
export function moveTourStep(current:number,direction:number){return Math.max(0,Math.min(recordingSteps.length-1,current+direction))}
export function tourKeyDirection(key:string,target:{tagName?:string;isContentEditable?:boolean},modified=false){
 if(modified||target.isContentEditable||['INPUT','TEXTAREA','SELECT','VIDEO','AUDIO'].includes(target.tagName??''))return 0;
 if(key==='ArrowLeft')return -1;if(key==='ArrowRight')return 1;
 if((key===' '||key==='Spacebar')&&!['BUTTON','A','SUMMARY'].includes(target.tagName??''))return 1;return 0;
}
